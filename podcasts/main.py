#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
import logging

from lib.config import Config
from lib.fetch.youtube import YouTubeFetcher
from lib.fetch.vimeo import process_vimeo_transcript, get_vimeo_data_headless, create_episode_metadata
from lib.generators.markdown import MarkdownGenerator
from lib.models.podcast import PodcastList, save_state, get_state
from lib.generators.id import IDGenerator

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
        
        # Check if URL exists and handle gracefully
        existing_entry = next((entry for entry in podcast_list.entries if entry.url == args.url), None)
        if existing_entry:
            print("\nPodcast already exists:")
            print(f"Episode ID: {existing_entry.episode_id}")
            print(f"Title: {existing_entry.title}")
            print(f"Podcast: {existing_entry.podcast_name}")
            print(f"Interviewee: {existing_entry.interviewee.name}")
            print(f"Status: {existing_entry.status}")
            print(f"Process Command: {existing_entry.process_command}")
            
            response = input("\nWould you like to overwrite this entry? (y/N): ")
            if response.lower() != 'y':
                print("Operation cancelled.")
                return
            
            # Store the existing ID for reuse
            existing_id = existing_entry.episode_id
            
            # Remove existing entry if user wants to overwrite
            podcast_list.entries.remove(existing_entry)
        else:
            existing_id = None
        
        # Get metadata based on platform
        if args.platform == "youtube":
            fetcher = YouTubeFetcher(api_key=os.getenv('YOUTUBE_API_KEY'))
            metadata = fetcher.get_video_data(args.url)
        elif args.platform == "vimeo":
            data = get_vimeo_data_headless(args.url)
            metadata = create_episode_metadata(data["playerConfig"]["video"]["id"], data)
        else:
            raise ValueError(f"Unsupported platform: {args.platform}")
        
        # Add entry to podcast list, passing the existing ID if we're overwriting
        entry = podcast_list.add_entry(args.url, args.platform, metadata, existing_id)
        
        print("\nPodcast added successfully!")
        print(f"Episode ID: {entry.episode_id}")
        print(f"Title: {entry.title}")
        print(f"Podcast: {entry.podcast_name}")
        print(f"Interviewee: {entry.interviewee.name}")
        print(f"\nRun next command:")
        print(f"{entry.process_command}")
        
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
    """Clean up all files for an episode"""
    try:
        podcast_list = PodcastList()
        entry = podcast_list.get_entry(episode_id)
        
        if not entry:
            print(f"No episode found with ID: {episode_id}")
            return
        
        # Remove files if they exist
        for file_path in [entry.episodes_file, entry.claims_file, entry.transcripts_file]:
            if file_path:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    print(f"Removed: {path}")
        
        # Reset entry status and file paths
        podcast_list.update_entry(
            episode_id,
            status="pending",
            episodes_file="",
            claims_file="",
            transcripts_file=""
        )
        
        # Reset ID cache after cleanup
        id_generator = IDGenerator()
        id_generator.reset_cache()
        
        print(f"Cleaned up all files for episode: {episode_id}")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")

def main():
    parser = argparse.ArgumentParser(description="Podcast processing tools")
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest="command")
    
    # Common arguments for all commands
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    # Add podcast
    add_parser = subparsers.add_parser("add-podcast", parents=[parent_parser])
    add_parser.add_argument("--platform", required=True, choices=["youtube", "vimeo"])
    add_parser.add_argument("--url", required=True)
    
    # Process podcast
    process_parser = subparsers.add_parser("process-podcast", parents=[parent_parser])
    process_parser.add_argument("--episode_id", required=True)
    
    # Cleanup podcast
    cleanup_parser = subparsers.add_parser("cleanup-podcast", parents=[parent_parser])
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