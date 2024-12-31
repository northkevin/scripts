import re
import json
import logging
from typing import Dict
from datetime import datetime

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.errors import HttpError

from ..config import Config

logger = logging.getLogger(__name__)

class YouTubeFetcher:
    def __init__(self, api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def get_video_data(self, url: str) -> Dict:
        """Get video metadata from YouTube"""
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {url}")
        
        try:
            response = self.youtube.videos().list(
                part='snippet,contentDetails',
                id=video_id
            ).execute()
            
            if not response['items']:
                raise ValueError(f"No video found for ID: {video_id}")
            
            video_data = response['items'][0]
            snippet = video_data['snippet']
            
            # Extract date and ensure it's a datetime
            published_at = datetime.strptime(
                snippet['publishedAt'], 
                '%Y-%m-%dT%H:%M:%SZ'
            )
            
            return {
                'title': snippet['title'],
                'description': snippet['description'],
                'published_at': published_at,
                'podcast_name': self._extract_podcast_name(snippet),
                'interviewee': {
                    'name': self._extract_interviewee_name(snippet),
                    'profession': self._extract_profession(snippet),
                    'organization': self._extract_organization(snippet)
                }
            }
            
        except HttpError as e:
            logger.error(f"YouTube API error: {str(e)}")
            raise ValueError(f"Failed to fetch video data: {str(e)}")
    
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
            r'youtube\.com/embed/([^&\n?#]+)',
            r'youtube\.com/v/([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            if match := re.search(pattern, url):
                return match.group(1)
        return ""
    
    def _extract_podcast_name(self, snippet: Dict) -> str:
        """Extract podcast name from video data"""
        channel_title = snippet.get('channelTitle', '')
        title = snippet.get('title', '')
        
        # Try to extract from title first
        if ' - ' in title:
            return title.split(' - ')[0].strip()
        
        return channel_title
    
    def _extract_interviewee_name(self, snippet: Dict) -> str:
        """Extract interviewee name from video data"""
        title = snippet.get('title', '')
        
        # Look for patterns like "Name - Topic" or "Show - Name - Topic"
        if ' - ' in title:
            parts = title.split(' - ')
            return parts[1] if len(parts) > 2 else parts[-1]
            
        return title
    
    def _extract_profession(self, snippet: Dict) -> str:
        """Extract profession from video description"""
        description = snippet.get('description', '')
        
        # Look for common profession indicators
        prof_indicators = ['PhD', 'Dr.', 'Professor', 'CEO', 'Founder']
        for indicator in prof_indicators:
            if indicator.lower() in description.lower():
                return indicator
        
        return ""
    
    def _extract_organization(self, snippet: Dict) -> str:
        """Extract organization from video description"""
        description = snippet.get('description', '')
        
        # Look for organization in parentheses
        org_match = re.search(r'\((.*?)\)', description)
        if org_match:
            return org_match.group(1)
            
        # Look for organization in description
        desc_lines = description.split('\n')[:5]
        for line in desc_lines:
            if any(x in line.lower() for x in ['university', 'institute', 'organization', 'company']):
                return line.strip()
                
        return ""

def get_youtube_transcript(url: str) -> str:
    """Get transcript from YouTube video"""
    logger.debug(f"Fetching transcript for URL: {url}")
    
    video_id = None
    for pattern in [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
        r'youtube\.com/embed/([^&\n?#]+)',
        r'youtube\.com/v/([^&\n?#]+)',
    ]:
        if match := re.search(pattern, url):
            video_id = match.group(1)
            break
            
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Debug: Save raw API response
        debug_file = Config.DIST_DIR / f"{video_id}_raw_api_response.txt"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("Raw YouTube Transcript API Response:\n")
            f.write("=" * 50 + "\n\n")
            json.dump(transcript_list, f, indent=2)
        
        formatted_lines = ["# Transcript\n"]
        formatted_lines.append("```timestamp-transcript")
        
        for item in transcript_list:
            start_time = f"{int(item['start']//3600):02d}:{int((item['start']%3600)//60):02d}:{item['start']%60:06.3f}"
            end_time = f"{int((item['start']+item['duration'])//3600):02d}:{int(((item['start']+item['duration'])%3600)//60):02d}:{(item['start']+item['duration'])%60:06.3f}"
            
            formatted_lines.extend([
                f"\n[{start_time} --> {end_time}]",
                f"{item['text']}"
            ])
            
        formatted_lines.append("\n```")
        return "\n".join(formatted_lines)
        
    except Exception as e:
        logger.error(f"Error fetching transcript: {str(e)}")
        raise ValueError(f"Could not get transcript: {str(e)}")