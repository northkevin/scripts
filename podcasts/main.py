#!/usr/bin/env python3

import argparse
import os
import json
from pathlib import Path

from fetch_vimeo import get_vimeo_data_headless
from transcript_utils import download_vtt_file
from generate_prompt import generate_prompt

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

def save_state(episode_id=None, transcript_file=None, metadata=None):
    """Save current episode state to help track progress between commands"""
    PODCAST_DATA.mkdir(exist_ok=True)
    
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)
    
    if episode_id:
        state["episode_id"] = episode_id
    if transcript_file:
        state["transcript_file"] = transcript_file
    if metadata:
        state["metadata"] = metadata
        
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_state():
    """Get current episode state"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
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
        
        # Save state and database
        save_state(episode_id=video_id, metadata=metadata)
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

def cmd_generate_prompt(args):
    """Generate ChatGPT prompt using saved state"""
    state = get_state()
    episode_id = args.episode_id or state.get("episode_id")
    transcript_file = args.transcript_file or state.get("transcript_file")
    
    # Try to use provided JSON file, then default database, then state
    json_file = args.json_file or DEFAULT_DB_FILE
    
    if not episode_id:
        print("Error: No episode_id provided or found in state")
        print("Hint: Run 'parse-episode' first or provide --episode_id")
        return
        
    if not transcript_file:
        print("Error: No transcript file found in state")
        print(f"Hint: Run 'get-transcript --episode_id {episode_id}' first")
        print("      or provide --transcript_file manually")
        return
    
    if not os.path.exists(transcript_file):
        print(f"Error: Transcript file not found: {transcript_file}")
        print(f"Hint: Check if the file exists or run 'get-transcript' again")
        return
        
    try:
        prompt = generate_prompt(episode_id, transcript_file, json_file)
        print("\n--- ChatGPT Prompt ---\n")
        print(prompt)
        print("\n-----------------------")
    except Exception as e:
        print(f"Error: {e}")
        print("Hint: Make sure you've completed the previous steps:")
        print("1. parse-episode - to get episode metadata")
        print("2. get-transcript - to download the transcript")
        print(f"3. Check that episode exists in database: {json_file}")

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
    
    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()