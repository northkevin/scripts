#!/usr/bin/env python3

import argparse
import os
import json
from pathlib import Path
import logging

from fetch_vimeo import get_vimeo_data_headless
from transcript_utils import download_vtt_file
from generate_prompt import generate_prompt
from fetch_youtube import YouTubeFetcher
from config import Config

# ------------------------------------------------------------
# Paths & State Management
# ------------------------------------------------------------
BASE_DIR = Path(__file__).parent
PODCAST_DATA = BASE_DIR / "Podcast Data"
TRANSCRIPTS_DIR = PODCAST_DATA / "transcripts"
STATE_FILE = PODCAST_DATA / ".current_episode.json"
DEFAULT_DB_FILE = PODCAST_DATA / "podcast_data.json"

EPISODE_SCHEMA = {
    "episode_id": "",
    "title": "",
    "share_url": "",
    "podcast_name": "",
    "interviewee": {
        "name": "<MANUAL>",
        "profession": "<MANUAL>",
        "organization": "<MANUAL>"
    },
    "air_date": "",
    "summary": "<MANUAL>",
    "claims": [],
    "related_topics": [],
    "tags": [],
    "webvtt_link": "",
    "transcript_file": ""
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("podcast_cli")

def get_state_file(platform_type: str = None) -> Path:
    """Get appropriate state file based on platform"""
    if platform_type == "youtube":
        return Config.YOUTUBE_STATE
    elif platform_type == "vimeo":
        return Config.VIMEO_STATE
    else:
        # Try to detect from existing state files
        if os.path.exists(Config.YOUTUBE_STATE):
            return Config.YOUTUBE_STATE
        if os.path.exists(Config.VIMEO_STATE):
            return Config.VIMEO_STATE
        # Default to YouTube if can't determine
        return Config.YOUTUBE_STATE

def save_state(platform_type: str = None, episode_id=None, transcript_file=None, metadata=None):
    """Save current episode state to platform-specific state file"""
    state_file = get_state_file(platform_type)
    state_file.parent.mkdir(exist_ok=True)
    
    state = {}
    if os.path.exists(state_file):
        with open(state_file) as f:
            state = json.load(f)
    
    if episode_id:
        state["episode_id"] = episode_id
    if transcript_file:
        state["transcript_file"] = transcript_file
    if metadata:
        state["metadata"] = metadata
        
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def get_state(platform_type: str = None) -> dict:
    """Get current episode state from appropriate platform file"""
    state_file = get_state_file(platform_type)
    if os.path.exists(state_file):
        with open(state_file) as f:
            return json.load(f)
    return {}

def save_to_database(metadata, db_file=DEFAULT_DB_FILE):
    """Save/update episode in the master database"""
    db_file.parent.mkdir(exist_ok=True)
    
    # Load existing database
    episodes = []
    if os.path.exists(db_file):
        with open(db_file) as f:
            episodes = json.load(f)
    
    # Update or add episode
    episode_id = metadata["episode_id"]
    for i, ep in enumerate(episodes):
        if ep["episode_id"] == episode_id:
            episodes[i].update(metadata)
            break
    else:
        episodes.append(metadata)
    
    # Save database
    with open(db_file, 'w') as f:
        json.dump(episodes, f, indent=2)

def create_episode_metadata(video_id, vimeo_data):
    """Create episode metadata using consistent schema"""
    player_data = vimeo_data["playerConfig"]
    ld_json_list = vimeo_data["ld_json"]
    ld_video = next((x for x in ld_json_list if x.get("@type") == "VideoObject"), {})
    
    # Start with template
    metadata = EPISODE_SCHEMA.copy()
    
    # Fill what we can from Vimeo
    metadata.update({
        "episode_id": str(video_id),
        "title": ld_video.get("name", player_data.get("video", {}).get("title", "")),
        "share_url": player_data.get("video", {}).get("share_url", ""),
        "podcast_name": player_data.get("video", {}).get("owner", {}).get("name", "<MANUAL>"),
        "air_date": ld_video.get("uploadDate", ""),
    })
    
    # Get transcript info if available
    text_tracks = player_data.get("request", {}).get("text_tracks", [])
    if text_tracks:
        url = text_tracks[0].get("url", "")
        if "/texttrack/" in url:
            texttrack_id = url.split("/texttrack/")[1].split(".")[0]
            token = url.split("token=")[1] if "token=" in url else None
            metadata["webvtt_link"] = f"https://player.vimeo.com/texttrack/{texttrack_id}.vtt?token={token}"
            metadata["transcript_info"] = {"texttrack_id": texttrack_id, "token": token}
    
    return metadata

# ------------------------------------------------------------
# Commands
# ------------------------------------------------------------
def cmd_parse_episode(args):
    """Parse basic data from Vimeo URL"""
    try:
        data = get_vimeo_data_headless(args.vimeo_url)
        video_id = str(data["playerConfig"].get("video", {}).get("id", "unknown"))
        
        # Create metadata using schema
        metadata = create_episode_metadata(video_id, data)
        metadata["platform_type"] = "vimeo"  # Add platform type
        
        # Save state and database
        save_state(
            platform_type="vimeo",
            episode_id=video_id,
            metadata=metadata
        )
        save_to_database(metadata)
        
        print("\nEpisode Info:")
        print(f"ID: {metadata['episode_id']}")
        print(f"Title: {metadata['title']}")
        print(f"Podcast: {metadata['podcast_name']}")
        
        if metadata.get("transcript_info"):
            print(f"\nTranscript available!")
            print(f"texttrack_id: {metadata['transcript_info']['texttrack_id']}")
            print(f"token: {metadata['transcript_info']['token']}")
            print("\nRun next command:")
            print(f"python main.py get-transcript --episode_id {video_id}")
        
        print("\nNote: Some fields need manual/ChatGPT completion:")
        print("- Interviewee details")
        print("- Summary")
        print("- Claims (after transcript)")
        print("- Related topics")
        print("- Tags")
        
    except Exception as e:
        print(f"Error: {e}")

def cmd_get_transcript(args):
    """Download transcript using saved state"""
    state = get_state()
    episode_id = args.episode_id or state.get("episode_id")
    if not episode_id:
        print("Error: No episode_id provided or found in state")
        return
        
    metadata = state.get("metadata", {})
    transcript_info = metadata.get("transcript_info")
    if not transcript_info:
        print("Error: No transcript info found in state")
        return
        
    try:
        TRANSCRIPTS_DIR.mkdir(exist_ok=True)
        out_path = TRANSCRIPTS_DIR / f"{episode_id}_transcript.vtt"
        
        webvtt_link = f"https://player.vimeo.com/texttrack/{transcript_info['texttrack_id']}.vtt?token={transcript_info['token']}"
        download_vtt_file(webvtt_link, str(out_path))
        
        # Save state for next command
        save_state(transcript_file=str(out_path))
        
        print(f"Transcript saved to: {out_path}")
        print("\nRun next command:")
        print(f"python main.py generate-prompt --episode_id {episode_id}")
        
    except Exception as e:
        print(f"Error: {e}")

def get_transcript_path(episode_id: str, platform_type: str = None) -> Path:
    """Get the appropriate transcript path based on platform"""
    if platform_type == "youtube":
        return Config.YOUTUBE_TRANSCRIPTS / f"{episode_id}_transcript.vtt"
    else:
        return Config.VIMEO_TRANSCRIPTS / f"{episode_id}_transcript.vtt"

def get_prompt_file(platform_type: str = None) -> Path:
    """Get path for saving the generated prompt"""
    if platform_type == "youtube":
        return Config.YOUTUBE_DIR / "current_episode_prompt.txt"
    else:
        return Config.VIMEO_DIR / "current_episode_prompt.txt"

def cmd_generate_prompt(args):
    """Generate ChatGPT prompt using saved state"""
    state = get_state()
    episode_id = args.episode_id or state.get("episode_id")
    transcript_file = args.transcript_file
    platform_type = state.get("metadata", {}).get("platform_type")
    
    # Try to use provided JSON file, then default database
    json_file = args.json_file or Config.DATABASE
    
    if not episode_id:
        print("Error: No episode_id provided or found in state")
        print("Hint: First run either:")
        print("- parse-youtube for YouTube videos")
        print("- parse-episode for Vimeo videos")
        return
    
    # If no transcript file provided, check platform-specific location
    if not transcript_file:
        transcript_file = str(get_transcript_path(episode_id, platform_type))
    
    if not os.path.exists(transcript_file):
        print(f"Error: Transcript file not found: {transcript_file}")
        print("\nHint: Check these locations:")
        print(f"YouTube: {Config.YOUTUBE_TRANSCRIPTS}/{episode_id}_transcript.vtt")
        print(f"Vimeo: {Config.VIMEO_TRANSCRIPTS}/{episode_id}_transcript.vtt")
        return
    
    try:
        # Generate the prompt
        prompt = generate_prompt(episode_id, transcript_file, json_file)
        
        # Save to platform-specific output file
        prompt_file = get_prompt_file(platform_type)
        with open(prompt_file, 'w') as f:
            f.write(prompt)
        
        print("\nPrompt generated successfully!")
        print(f"Saved to: {prompt_file}")
        print("\nPreview (first 500 chars):")
        print("-" * 40)
        print(prompt[:500] + "...")
        print("-" * 40)
        print(f"\nFull prompt available in: {prompt_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nHint: Make sure you've completed these steps:")
        if platform_type == "youtube":
            print("1. Run parse-youtube to get video data and transcript")
        else:
            print("1. Run parse-episode to get video data")
            print("2. Run get-transcript to download the transcript")
        print(f"\nThen check that episode exists in: {json_file}")

def cmd_parse_youtube(args):
    """Parse YouTube video and download transcript"""
    try:
        fetcher = YouTubeFetcher(
            Config.YOUTUBE_TRANSCRIPTS,
            api_key=os.getenv('YOUTUBE_API_KEY')
        )
        metadata = fetcher.get_video_data(args.url)
        
        if not metadata:
            raise Exception("Failed to get video metadata")
        
        # Save to platform-specific state
        save_state(
            platform_type="youtube",
            episode_id=metadata["episode_id"],
            metadata=metadata
        )
        save_to_database(metadata)
        
        print("\nVideo Info:")
        print(f"ID: {metadata['episode_id']}")
        print(f"Title: {metadata.get('title', 'Unknown')}")
        print(f"Channel: {metadata.get('podcast_name', 'Unknown')}")
        
        if metadata.get("transcript_file"):
            print(f"\nTranscript saved to: {metadata['transcript_file']}")
            print("\nRun next command to generate prompt:")
            print("python main.py generate-prompt")
        else:
            print("\nNo transcript available for this video")
            
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback
            print("\nFull traceback:")
            print(traceback.format_exc())

def main():
    parser = argparse.ArgumentParser(description="Podcast processing tools")
    subparsers = parser.add_subparsers(dest="command")
    
    # Parse episode
    parse_parser = subparsers.add_parser("parse-episode")
    parse_parser.add_argument("--vimeo_url", required=True)
    parse_parser.set_defaults(func=cmd_parse_episode)
    
    # Get transcript (now uses saved state)
    transcript_parser = subparsers.add_parser("get-transcript")
    transcript_parser.add_argument("--episode_id", help="Optional if state exists")
    transcript_parser.set_defaults(func=cmd_get_transcript)
    
    # Generate prompt (uses saved state)
    prompt_parser = subparsers.add_parser("generate-prompt")
    prompt_parser.add_argument("--episode_id", help="Optional if state exists")
    prompt_parser.add_argument("--transcript_file", help="Optional if state exists")
    prompt_parser.add_argument("--json_file", help="Optional JSON database file")
    prompt_parser.set_defaults(func=cmd_generate_prompt)
    
    # Parse YouTube
    youtube_parser = subparsers.add_parser("parse-youtube",
        help="Parse YouTube video and download transcript")
    youtube_parser.add_argument("--url", required=True,
        help="YouTube video URL")
    youtube_parser.add_argument("--debug", action="store_true",
        help="Run in debug mode (shows browser)")
    youtube_parser.add_argument("--initial-wait", type=int, default=10,
        help="Initial page load wait time in seconds")
    youtube_parser.add_argument("--element-wait", type=int, default=5,
        help="Wait time for individual elements in seconds")
    youtube_parser.add_argument("--retries", type=int, default=3,
        help="Number of retry attempts")
    youtube_parser.set_defaults(func=cmd_parse_youtube)
    
    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()