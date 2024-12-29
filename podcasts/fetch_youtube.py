from typing import Dict, Any
import logging
from pathlib import Path
from datetime import datetime

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import WebVTTFormatter

from schema import EPISODE_TEMPLATE

logger = logging.getLogger("podcast_cli")

class YouTubeFetcher:
    def __init__(self, download_dir: Path, api_key: str = None):
        """
        Initialize YouTube fetcher.
        Get API key from: https://console.cloud.google.com/apis/credentials
        """
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.api_key = api_key
        if api_key:
            self.youtube = build('youtube', 'v3', developerKey=api_key)
        else:
            logger.warning("No YouTube API key provided. Some features will be limited.")
        
    def get_video_data(self, url: str) -> Dict[str, Any]:
        """Get video metadata and transcript using APIs"""
        try:
            # Extract video ID from URL
            video_id = url.split("v=")[1].split("&")[0]
            logger.info(f"Getting data for video: {video_id}")
            
            # Get video metadata from API
            if self.api_key:
                metadata = self._get_api_metadata(video_id)
            else:
                metadata = self._get_basic_metadata(video_id)
                
            if not metadata:
                raise Exception("Failed to get video metadata")
            
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
            
    def _get_api_metadata(self, video_id: str) -> Dict[str, Any]:
        """Get detailed metadata using YouTube Data API"""
        try:
            video_response = self.youtube.videos().list(
                part='snippet,contentDetails',
                id=video_id
            ).execute()
            
            if not video_response.get('items'):
                raise Exception(f"Video {video_id} not found")
                
            video_data = video_response['items'][0]
            snippet = video_data['snippet']
            
            metadata = EPISODE_TEMPLATE.copy()
            metadata.update({
                "episode_id": video_id,
                "platform_type": "youtube",
                "title": snippet['title'],
                "share_url": f"https://www.youtube.com/watch?v={video_id}",
                "podcast_name": snippet['channelTitle'],
                "air_date": snippet['publishedAt'],
                "duration": video_data['contentDetails']['duration'],
                "summary": snippet['description'],
                "tags": snippet.get('tags', []),
                "related_topics": [
                    snippet.get('categoryId', ''),
                    *snippet.get('tags', [])[:5]  # Use first 5 tags as topics
                ]
            })
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting API metadata: {e}")
            return None
        
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