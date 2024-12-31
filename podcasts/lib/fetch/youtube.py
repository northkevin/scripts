import os
from pathlib import Path
import logging
from typing import Dict, Optional

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

from ..config import Config

logger = logging.getLogger(__name__)

class YouTubeFetcher:
    def __init__(self, output_dir: Path = Config.TRANSCRIPTS_DIR, api_key: Optional[str] = None):
        self.output_dir = output_dir
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        
        if not self.api_key:
            raise ValueError("YouTube API key is required")
    
    def get_video_data(self, url: str) -> Dict:
        """Get video metadata and transcript"""
        video_id = self._extract_video_id(url)
        
        # Get video details from API
        youtube = build('youtube', 'v3', developerKey=self.api_key)
        
        try:
            # Get video metadata
            video_response = youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()
            
            if not video_response['items']:
                raise ValueError(f"No video found for ID: {video_id}")
            
            video_data = video_response['items'][0]['snippet']
            
            # Get transcript
            transcript_path = self._get_transcript(video_id)
            
            # Format metadata
            metadata = {
                'title': video_data['title'],
                'description': video_data['description'],
                'channel_title': video_data['channelTitle'],
                'published_at': video_data['publishedAt'],
                'transcript_file': str(transcript_path) if transcript_path else None
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error fetching YouTube data: {str(e)}")
            raise
    
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        if "youtu.be" in url:
            return url.split("/")[-1]
        elif "v=" in url:
            return url.split("v=")[1].split("&")[0]
        else:
            raise ValueError(f"Could not extract video ID from URL: {url}")
    
    def _get_transcript(self, video_id: str) -> Optional[Path]:
        """Download video transcript"""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Convert to markdown format
            output_path = self.output_dir / f"{video_id}_transcript.md"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# Transcript\n\n")
                for entry in transcript:
                    # Skip timestamps and write only text
                    f.write(f"{entry['text']}\n\n")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
            return None