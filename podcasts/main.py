#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
import logging

from lib.config import Config
from lib.fetch.youtube import YouTubeFetcher, get_youtube_transcript
from lib.fetch.vimeo import process_vimeo_transcript, get_vimeo_data_headless, create_episode_metadata
from lib.generators.markdown import MarkdownGenerator
from lib.models.podcast import PodcastList, save_state
from lib.generators.id import IDGenerator

logger = logging.getLogger(__name__)

def process_youtube_transcript(entry) -> Path:
    """Process YouTube transcript"""
    try:
        transcript_text = get_youtube_transcript(entry.url)
        
        # Debug: Save raw transcript data
        debug_file = Config.DIST_DIR / f"{entry.episode_id}_raw_transcript_debug.txt"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(f"Debug Output for {entry.url}\n")
            f.write("=" * 50 + "\n\n")
            f.write(transcript_text)
        logger.debug(f"Saved raw transcript debug data to: {debug_file}")
        
        # Save transcript using config path
        transcript_file = Config.get_transcript_path(entry.episode_id)
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        return transcript_file
        
    except Exception as e:
        raise ValueError(f"Could not get transcript: {str(e)}")

def cmd_add_podcast(args):
    """Add new podcast to master list"""
    try:
        podcast_list = PodcastList()
        
        # Check if URL exists
        existing_entry = next((entry for entry in podcast_list.entries if entry.url == args.url), None)
        if existing_entry:
            print("\nPodcast already exists:")
            print(f"Episode ID: {existing_entry.episode_id}")
            print(f"Title: {existing_entry.title}")
            print(f"Podcast: {existing_entry.podcast_name}")
            print(f"Interviewee: {existing_entry.interviewee.name}")
            print(f"Status: {existing_entry.status}")
            print(f"Process Command: {existing_entry.process_command}")
            
            if input("\nWould you like to overwrite this entry? (y/N): ").lower() != 'y':
                print("Operation cancelled.")
                return
            
            # Store existing ID and remove entry
            existing_id = existing_entry.episode_id
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
        
        # Add entry to podcast list
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
        podcast_list = PodcastList()
        markdown_gen = MarkdownGenerator()
        
        entry = podcast_list.get_entry(args.episode_id)
        if not entry:
            raise ValueError(f"Episode {args.episode_id} not found")
        
        # Ensure directories exist
        Config.ensure_dirs()
        
        # Save initial state
        save_state(args.episode_id)
        
        try:
            # Generate transcript based on platform
            transcript_file = (process_youtube_transcript(entry) 
                             if entry.platform == "youtube" 
                             else process_vimeo_transcript(entry))
            
            # Update transcript file path
            podcast_list.update_entry(args.episode_id, transcripts_file=str(transcript_file))
            
            # Generate episode markdown
            episode_file = markdown_gen.generate_episode_markdown(entry)
            podcast_list.update_entry(args.episode_id, episodes_file=str(episode_file))
            
            # Final state update
            save_state(args.episode_id, status="complete")
            
            print("\nProcessing completed successfully!")
            print(f"\nFiles created:")
            print(f"1. Episode:    {episode_file}")
            print(f"2. Transcript: {transcript_file}")
            print(f"\nPodcast data stored in: {Config.PODCAST_LIST}")
            print(f"Episode ID: {entry.episode_id}")
            
        except Exception as e:
            save_state(args.episode_id, status="error", error=str(e))
            podcast_list.update_entry(args.episode_id, status="error")
            raise
        
    except Exception as e:
        print(f"Error: {e}")

def cleanup_episode(episode_id: str):
    """Clean up all files for an episode and remove from database"""
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
        
        # Remove entry and reset ID cache
        podcast_list.entries.remove(entry)
        podcast_list._save()
        IDGenerator().reset_cache()
        
        print(f"\nCleanup completed successfully!")
        print(f"Removed episode: {entry.title}")
        print(f"Episode ID: {episode_id}")
        print(f"Removed from database: {Config.PODCAST_LIST}")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")

def main():
    parser = argparse.ArgumentParser(description="Podcast processing tools")
    subparsers = parser.add_subparsers(dest="command")
    
    # Add debug flag to main parser
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
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
    
    # Configure logging
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