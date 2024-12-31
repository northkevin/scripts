from typing import Dict, Any
import logging
from pathlib import Path
from datetime import datetime
import re

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import WebVTTFormatter

from schema import EPISODE_TEMPLATE
from podcasts.lib.config import Config

logger = logging.getLogger("podcast_cli")

class YouTubeFetcher:
    def __init__(self, download_dir: Path = None, api_key: str = None):
        """Initialize YouTube fetcher"""
        self.download_dir = download_dir or Config.YOUTUBE_TRANSCRIPTS
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.api_key = api_key
        if api_key:
            self.youtube = build('youtube', 'v3', developerKey=api_key)
        else:
            logger.warning("No YouTube API key provided. Some features will be limited.")

    def _extract_interviewee_info(self, title: str, description: str) -> Dict[str, str]:
        """
        Extract interviewee information from video title and description.
        
        Common patterns:
        - "Interview with Dr. John Smith"
        - "Dr. Jane Doe: Topic"
        - "Title | Dr. John Smith"
        - "Title w/ Dr. Jane Doe"
        """
        interviewee = {
            "name": "",
            "profession": "",
            "organization": ""
        }
        
        # Common title patterns for extracting names
        patterns = [
            r"(?:with|w/)\s+([^|:]+?)(?:\||$|\s+on\s+|\s+about\s+)",  # "with Dr. John Smith" or "w/ Dr. John Smith"
            r"[|]\s*([^|:]+?)(?:\||$|\s+on\s+|\s+about\s+)",  # "| Dr. John Smith"
            r"[:]\s*([^|:]+?)(?:\||$|\s+on\s+|\s+about\s+)",  # ": Dr. John Smith"
            r"(?:featuring|ft\.|ft|feat\.?)\s+([^|:]+?)(?:\||$|\s+on\s+|\s+about\s+)",  # "featuring Dr. John Smith"
        ]
        
        # Try to extract name from title
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                interviewee["name"] = match.group(1).strip()
                break
        
        # If no name found in title, try description
        if not interviewee["name"]:
            # Look for common biography indicators in description
            bio_patterns = [
                r"(?:About|Bio|Biography|Guest):\s*([^.\n]+)",
                r"([^.\n]+) is (?:a|an) (?:renowned|expert|leading|prominent)",
                r"Dr\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+"
            ]
            
            for pattern in bio_patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    interviewee["name"] = match.group(1).strip()
                    break
        
        # Extract profession and organization from description
        if interviewee["name"]:
            name = interviewee["name"]
            # Look for profession/title near the name
            prof_pattern = f"{name} is (?:a|an) ([^.,]+)"
            prof_match = re.search(prof_pattern, description, re.IGNORECASE)
            if prof_match:
                interviewee["profession"] = prof_match.group(1).strip()
            
            # Look for organization
            org_patterns = [
                f"{name}[^.]*?(?:at|with|of) (?:the )?([A-Z][A-Za-z ]+(?:Institute|University|Center|Hospital|Foundation|Lab|Corporation|Inc\.|LLC|Ltd\.|Company))",
                f"{name}[^.]*?(?:founder of|created) (?:the )?([A-Z][A-Za-z ]+(?:Institute|Center|Foundation|Lab|Corporation|Inc\.|LLC|Ltd\.|Company))"
            ]
            
            for pattern in org_patterns:
                org_match = re.search(pattern, description)
                if org_match:
                    interviewee["organization"] = org_match.group(1).strip()
                    break
        
        # Clean up the name if needed
        if interviewee["name"]:
            # Remove common prefixes if they appear in middle of name
            interviewee["name"] = re.sub(r'\s+(?:Dr\.|Professor|Prof\.|MD|PhD)\s+', ' ', 
                                       f' {interviewee["name"]} ').strip()
            
            # Add back Dr. prefix if it was in original
            if re.search(r'(?:^|\s)Dr\.?\s', title):
                interviewee["name"] = f"Dr. {interviewee['name']}"
        
        return interviewee

    def get_video_data(self, url: str) -> Dict[str, Any]:
        """Get video metadata and transcript using APIs"""
        try:
            # Extract video ID from URL
            video_id = url.split("v=")[1].split("&")[0]
            logger.info(f"Getting data for video: {video_id}")
            
            # Get video metadata from API
            if self.api_key:
                video_response = self.youtube.videos().list(
                    part='snippet,contentDetails',
                    id=video_id
                ).execute()
                
                if not video_response.get('items'):
                    raise Exception(f"Video {video_id} not found")
                    
                video_data = video_response['items'][0]
                snippet = video_data['snippet']
                
                # Extract interviewee information
                interviewee = self._extract_interviewee_info(
                    snippet['title'],
                    snippet['description']
                )
                
                metadata = EPISODE_TEMPLATE.copy()
                metadata.update({
                    "episode_id": video_id,
                    "platform_type": "youtube",
                    "title": snippet['title'],
                    "share_url": f"https://www.youtube.com/watch?v={video_id}",
                    "podcast_name": snippet['channelTitle'],
                    "interviewee": interviewee,
                    "air_date": snippet['publishedAt'],
                    "duration": video_data['contentDetails']['duration'],
                    "summary": snippet['description'],
                    "tags": snippet.get('tags', []),
                    "related_topics": [
                        snippet.get('categoryId', ''),
                        *snippet.get('tags', [])[:5]  # Use first 5 tags as topics
                    ]
                })
            else:
                metadata = self._get_basic_metadata(video_id)
            
            # Get transcript
            transcript = self._get_transcript(video_id)
            if transcript:
                try:
                    # Save transcript as VTT
                    vtt_path = self.download_dir / f"{video_id}_transcript.vtt"
                    self._save_transcript(transcript, vtt_path)
                    metadata["transcript_file"] = str(vtt_path)
                    metadata.pop("webvtt_link", None)  # Remove if exists
                    logger.info(f"Saved transcript to {vtt_path}")
                except Exception as e:
                    logger.error(f"Error saving transcript: {e}")
            else:
                logger.warning("No transcript available for this video")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error fetching YouTube data: {e}")
            raise

    def _get_basic_metadata(self, video_id: str) -> Dict[str, Any]:
        """Get basic metadata without API"""
        metadata = EPISODE_TEMPLATE.copy()
        metadata.update({
            "episode_id": video_id,
            "platform_type": "youtube",
            "share_url": f"https://www.youtube.com/watch?v={video_id}",
        })
        return metadata
        
    def _get_transcript(self, video_id: str) -> list:
        """Get transcript using youtube_transcript_api"""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            logger.info("Successfully retrieved transcript")
            return transcript_list
        except Exception as e:
            logger.warning(f"Could not get transcript: {e}")
            return None
            
    def _save_transcript(self, transcript: list, output_path: Path):
        """Save transcript in WebVTT format"""
        try:
            formatter = WebVTTFormatter()
            vtt_formatted = formatter.format_transcript(transcript)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(vtt_formatted)
            logger.info(f"Transcript saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving transcript: {e}")
            raise 