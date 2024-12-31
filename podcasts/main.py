#!/usr/bin/env python3

import argparse
import os
from datetime import datetime
import json
from pathlib import Path
import logging

from config import Config
from fetch_youtube import YouTubeFetcher
from fetch_vimeo import process_vimeo_transcript, get_vimeo_data_headless, create_episode_metadata
from generate_markdown import MarkdownGenerator
from podcast_list import PodcastList, save_state, get_state

logger = logging.getLogger(__name__)

def process_youtube_transcript(entry) -> Path:
    """Process YouTube transcript"""
    fetcher = YouTubeFetcher(
        Config.TRANSCRIPTS_DIR,
        api_key=os.getenv('YOUTUBE_API_KEY')
    )
    video_id = entry.url.split("v=")[1].split("&")[0]
    metadata = fetcher.get_video_data(entry.url)
    
    if not metadata.get('transcript_file'):
        raise Exception("No transcript available for this video")
    
    # Rename the transcript file to use episode_id
    old_path = Path(metadata['transcript_file'])
    new_path = Config.TRANSCRIPTS_DIR / f"{entry.episode_id}_transcript.md"
    
    if old_path.exists():
        old_path.rename(new_path)
    
    return new_path

def cmd_add_podcast(args):
    """Add new podcast to master list"""
    try:
        # Initialize podcast list
        podcast_list = PodcastList()
        
        # Get metadata based on platform
        if args.platform == "youtube":
            fetcher = YouTubeFetcher(api_key=os.getenv('YOUTUBE_API_KEY'))
            metadata = fetcher.get_video_data(args.url)
        elif args.platform == "vimeo":
            data = get_vimeo_data_headless(args.url)
            metadata = create_episode_metadata(data["playerConfig"]["video"]["id"], data)
        else:
            raise ValueError(f"Unsupported platform: {args.platform}")
        
        # Add entry to podcast list
        entry = podcast_list.add_entry(args.url, args.platform, metadata)
        
        print("\nPodcast added successfully!")
        print(f"Episode ID: {entry.episode_id}")
        print(f"Title: {entry.title}")
        print(f"Podcast: {entry.podcast_name}")
        print(f"Interviewee: {entry.interviewee.name}")
        print(f"\nRun next command to process content:")
        print(f"python main.py process-podcast --episode_id {entry.episode_id}")
        
    except Exception as e:
        print(f"Error: {e}")

def cmd_process_podcast(args):
    """Process podcast content"""
    try:
        # Initialize podcast list and markdown generator
        podcast_list = PodcastList()
        markdown_gen = MarkdownGenerator()
        
        # Get entry
        entry = podcast_list.get_entry(args.episode_id)
        if not entry:
            raise ValueError(f"Episode {args.episode_id} not found")
        
        # Save initial state
        save_state(args.episode_id)
        
        try:
            # Generate transcript based on platform
            if entry.platform == "youtube":
                transcript_file = process_youtube_transcript(entry)
            else:
                transcript_file = process_vimeo_transcript(entry)
            
            # Update transcript file path
            podcast_list.update_entry(
                args.episode_id,
                transcripts_file=str(transcript_file)
            )
            
            # Generate episode markdown
            episode_file = markdown_gen.generate_episode_markdown(entry)
            podcast_list.update_entry(
                args.episode_id,
                episodes_file=str(episode_file)
            )
            
            # Generate claims markdown
            claims_file = markdown_gen.generate_claims_markdown(entry)
            podcast_list.update_entry(
                args.episode_id,
                claims_file=str(claims_file)
            )
            
            # Final state update
            save_state(args.episode_id, status="complete")
            
        except Exception as e:
            # Update state and master list on error
            save_state(args.episode_id, status="error", error=str(e))
            podcast_list.update_entry(args.episode_id, status="error")
            raise
        
    except Exception as e:
        print(f"Error: {e}")

def cleanup_episode(episode_id: str):
    """Remove all files associated with an episode ID"""
    try:
        # Initialize podcast list
        podcast_list = PodcastList()
        
        # Get entry
        entry = podcast_list.get_entry(episode_id)
        if not entry:
            print(f"No entry found for episode ID: {episode_id}")
            return
        
        files_to_remove = [
            Path(entry.episodes_file) if entry.episodes_file else None,
            Path(entry.claims_file) if entry.claims_file else None,
            Config.TRANSCRIPTS_DIR / f"{episode_id}_transcript.md"
        ]
        
        for file_path in files_to_remove:
            if file_path and file_path.exists():
                file_path.unlink()
                print(f"Removed: {file_path}")
        
        # Reset entry status and file paths
        podcast_list.update_entry(
            episode_id,
            status="pending",
            episodes_file="",
            claims_file="",
            transcripts_file=""
        )
        
        print(f"Cleaned up all files for episode: {episode_id}")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")

def main():
    parser = argparse.ArgumentParser(description="Podcast processing tools")
    
    # Add debug flag at the top level
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest="command")
    
    # Add podcast
    add_parser = subparsers.add_parser("add-podcast")
    add_parser.add_argument("--platform", required=True, choices=["youtube", "vimeo"])
    add_parser.add_argument("--url", required=True)
    
    # Process podcast
    process_parser = subparsers.add_parser("process-podcast")
    process_parser.add_argument("--episode_id", required=True)
    
    # Cleanup podcast
    cleanup_parser = subparsers.add_parser("cleanup-podcast")
    cleanup_parser.add_argument("--episode_id", required=True)
    
    args = parser.parse_args()
    
    # Configure logging based on debug flag
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    if args.command:
        if args.command == "add-podcast":
            cmd_add_podcast(args)
        elif args.command == "process-podcast":
            cmd_process_podcast(args)
        elif args.command == "cleanup-podcast":
            cleanup_episode(args.episode_id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()