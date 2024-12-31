import logging
import re
import json
import time
import requests
import datetime

from typing import Dict, Any
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..config import Config

logger = logging.getLogger(__name__)

def _parse_ld_json(page_source: str) -> list:
    """Extract and parse ld+json data from page source."""
    pattern = r'<script type="application\/ld\+json">(.*?)<\/script>'
    matches = re.finditer(pattern, page_source, re.DOTALL)
    results = []
    
    for match in matches:
        try:
            data = json.loads(match.group(1))
            results.append(data)
        except json.JSONDecodeError:
            logger.warning("Failed to parse ld+json block")
            continue
            
    return results

def _extract_player_config(page_source: str) -> str:
    """Extract the JSON for window.playerConfig using balanced brace approach."""
    logger.debug("Using balanced brace approach for window.playerConfig.")

    start_match = re.search(r'window\.playerConfig\s*=\s*\{', page_source)
    if not start_match:
        logger.debug("No match for 'window.playerConfig = {' in page source.")
        raise ValueError("No window.playerConfig found.")

    start_index = start_match.end() - 1  # position of the '{'
    brace_count = 0
    end_index = None

    for i, ch in enumerate(page_source[start_index:], start=start_index):
        if ch == '{':
            brace_count += 1
        elif ch == '}':
            brace_count -= 1
            if brace_count == 0:
                end_index = i
                break

    if end_index is None:
        logger.debug("Couldn't find matching '}' for playerConfig.")
        raise ValueError("Could not find matching '}' for playerConfig JSON.")

    raw_json = page_source[start_index:end_index+1]
    logger.debug("Captured window.playerConfig (partial debug): %s", raw_json[:500])
    return raw_json

def get_vimeo_data_headless(vimeo_url: str) -> Dict[str, Any]:
    """Get Vimeo video data using headless browser."""
    logger.debug(f"Initializing headless browser to load: {vimeo_url}")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(vimeo_url)
        time.sleep(3)  # wait for JavaScript

        page_source = driver.page_source
        logger.debug("Headless browser page_source length=%d", len(page_source))

        # Extract playerConfig
        raw_json = _extract_player_config(page_source)
        player_data = json.loads(raw_json)
        logger.debug("Successfully parsed window.playerConfig.")

        # Extract LD+JSON data
        ld_json_list = _parse_ld_json(page_source)
        logger.debug("Found %d ld+json blocks.", len(ld_json_list))

        return {
            "playerConfig": player_data,
            "ld_json": ld_json_list,
            "page_source": page_source
        }
    finally:
        logger.debug("Quitting headless browser.")
        driver.quit()

def create_episode_metadata(video_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized metadata from Vimeo data"""
    logger.debug("Starting metadata creation for video_id: %s", video_id)
    
    video_data = data["playerConfig"].get("video", {})
    ld_json_data = next((item for item in data.get("ld_json", []) 
                        if item.get("@type") == "VideoObject"), {})
    
    # Extract title and try to parse interviewee info
    title = ld_json_data.get("name") or video_data.get('title', '')
    
    # Try to extract interviewee name from title
    interviewee_name = "<MANUAL>"
    if "PODCAST |" in title:
        # Format: "PODCAST | JACK KRUSE"
        parts = title.split("|")
        if len(parts) > 1:
            interviewee_name = parts[1].strip()
    elif "with" in title.lower():
        # Format: "Podcast with Jack Kruse"
        parts = title.lower().split("with")
        if len(parts) > 1:
            interviewee_name = parts[1].strip().title()
    
    # Get owner info for potential organization
    owner_data = video_data.get("owner", {})
    owner_name = owner_data.get("name", "")
    
    # Get upload date
    upload_date = (
        ld_json_data.get("uploadDate", "").split("T")[0] or
        video_data.get("upload_date") or
        datetime.now().strftime("%Y-%m-%d")
    )
    
    metadata = {
        "episode_id": str(video_id),
        "platform_type": "vimeo",
        "title": title,
        "share_url": f"https://vimeo.com/{video_id}",
        "podcast_name": owner_name,
        "interviewee": {
            "name": interviewee_name,
            "profession": "<MANUAL>",
            "organization": "<MANUAL>"
        },
        "published_at": upload_date,
        "duration": video_data.get("duration", ""),
        "summary": ld_json_data.get("description") or video_data.get("description", ""),
        "tags": video_data.get("tags", []),
        "related_topics": video_data.get("tags", [])[:5]
    }
    
    # Extract transcript info from request.text_tracks in playerConfig
    logger.debug("Looking for request.text_tracks in playerConfig...")
    
    request_data = data["playerConfig"].get("request", {})
    if "text_tracks" in request_data:
        text_tracks = request_data["text_tracks"]
        logger.debug("Found text_tracks in request: %s", json.dumps(text_tracks, indent=2))
        
        if text_tracks and len(text_tracks) > 0:
            track = text_tracks[0]  # Get first track
            track_url = track.get("url", "")
            logger.debug("Found track URL: %s", track_url)
            
            if "/texttrack/" in track_url:
                texttrack_id = track_url.split("/texttrack/")[1].split(".")[0]
                token = track_url.split("token=")[1] if "token=" in track_url else None
                logger.debug("Extracted texttrack_id: %s, token: %s", texttrack_id, token)
                
                metadata["transcript_info"] = {
                    "texttrack_id": texttrack_id,
                    "token": token
                }
                # Use the full player.vimeo.com URL
                metadata["webvtt_link"] = f"https://player.vimeo.com{track_url}"
                logger.debug("Created webvtt_link: %s", metadata["webvtt_link"])
    else:
        logger.warning("No text_tracks found in playerConfig.request")
        logger.debug("Available request keys: %s", list(request_data.keys()))
    
    if "webvtt_link" not in metadata:
        logger.warning("Failed to create webvtt_link")
        
    return metadata

def process_vimeo_transcript(entry) -> Path:
    """Process Vimeo transcript"""
    logger.debug("Starting Vimeo transcript processing for entry: %s", entry.episode_id)
    
    data = get_vimeo_data_headless(entry.url)
    metadata = create_episode_metadata(
        data["playerConfig"]["video"]["id"],
        data
    )
    
    if not metadata.get('webvtt_link'):
        logger.error("No webvtt_link found in metadata")
        raise Exception("No transcript available for this video")
    
    # Save directly as markdown file
    transcript_path = Config.TRANSCRIPTS_DIR / f"{entry.episode_id}_transcript.md"
    logger.debug(f"Will save transcript to: {transcript_path}")
    
    try:
        # Download VTT content
        response = requests.get(metadata['webvtt_link'])
        response.raise_for_status()
        vtt_content = response.text
        logger.debug("Successfully downloaded VTT content")
        
        # Convert to markdown
        md_content = ["# Transcript\n\n"]
        lines = vtt_content.splitlines()
        
        # Skip the VTT header
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() == "":
                start_idx = i + 1
                break
        
        current_text = []
        for line in lines[start_idx:]:
            line = line.strip()
            
            # Skip timestamp lines and empty lines
            if not line or '-->' in line or line.replace('-', '').isnumeric():
                if current_text:
                    md_content.append(' '.join(current_text) + '\n\n')
                    current_text = []
                continue
                
            current_text.append(line)
        
        # Add any remaining text
        if current_text:
            md_content.append(' '.join(current_text) + '\n\n')
        
        # Write markdown file
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.writelines(md_content)
        
        logger.debug(f"Saved transcript as markdown: {transcript_path}")
        return transcript_path
        
    except Exception as e:
        logger.error(f"Failed to process transcript: {str(e)}")
        raise