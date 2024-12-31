import os
from pathlib import Path
import logging
from typing import Dict, Optional, Any
import json
import re

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.errors import HttpError

from ..config import Config

logger = logging.getLogger(__name__)

def get_youtube_transcript(url: str) -> str:
    """Get transcript from YouTube video"""
    # Extract video ID using regex directly
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
        r'youtube\.com/embed/([^&\n?#]+)',
        r'youtube\.com/v/([^&\n?#]+)',
    ]
    
    video_id = None
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
            
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return "\n".join(f"{item['text']}" for item in transcript_list)
    except Exception as e:
        raise ValueError(f"Could not get transcript: {str(e)}")


class YouTubeFetcher:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("YouTube API key is required")
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.logger = logging.getLogger(__name__)
    
    def get_video_data(self, url: str) -> Dict[str, Any]:
        """Get video data from YouTube"""
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {url}")
            
        try:
            # Get video details from API
            request = self.youtube.videos().list(
                part="snippet,contentDetails",
                id=video_id
            )
            response = request.execute()
            
            if not response['items']:
                raise ValueError(f"No video found with ID: {video_id}")
                
            video_data = response['items'][0]
            snippet = video_data['snippet']
            
            # Extract interviewee info from title
            title = snippet['title']
            interviewee_name = "Unknown"
            
            # Try different title patterns
            if "|" in title:
                # Format: "Title | Person Name"
                parts = title.split("|")
                if len(parts) > 1:
                    interviewee_name = parts[1].strip()
            elif "with" in title.lower():
                # Format: "Interview with Person Name"
                parts = title.lower().split("with")
                if len(parts) > 1:
                    interviewee_name = parts[1].strip().title()
            elif ":" in title:
                # Format: "Title: Person Name on Topic"
                parts = title.split(":")
                if len(parts) > 1:
                    name_part = parts[1].split(" on ")[0].strip()
                    if name_part:
                        interviewee_name = name_part
            
            # Try to extract from description
            if interviewee_name == "Unknown" and "guest:" in snippet['description'].lower():
                desc_lines = snippet['description'].split('\n')
                for line in desc_lines:
                    if "guest:" in line.lower():
                        interviewee_name = line.split(":", 1)[1].strip()
                        break
            
            # Extract podcast name from channel
            podcast_name = snippet.get('channelTitle', 'Unknown Podcast')
            
            # Create standardized metadata
            metadata = {
                'title': title,
                'published_at': snippet['publishedAt'],
                'podcast_name': podcast_name,
                'interviewee': {
                    'name': interviewee_name,
                    'profession': self._extract_profession(title, snippet['description']),
                    'organization': self._extract_organization(title, snippet['description'])
                },
                'description': snippet['description'],
                'tags': snippet.get('tags', []),
                'duration': video_data['contentDetails']['duration']
            }
            
            self.logger.debug(f"Extracted metadata: {json.dumps(metadata, indent=2)}")
            return metadata
            
        except HttpError as e:
            raise ValueError(f"YouTube API error: {e.resp.status} - {e.content}")
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from URL"""
        # Handle different URL formats
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
            r'youtube\.com/embed/([^&\n?#]+)',
            r'youtube\.com/v/([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _extract_profession(self, title: str, description: str) -> str:
        """Extract profession from title or description"""
        # Common professional titles and specialties
        base_titles = {
            'Dr': 'Doctor',
            'Professor': 'Professor',
            'PhD': 'PhD',
            'MD': 'Medical Doctor',
            'Scientist': 'Scientist',
            'Researcher': 'Researcher',
            'Expert': 'Expert'
        }
        
        specialties = [
            'Brain Surgeon', 'Neurosurgeon', 'Surgeon',
            'Physicist', 'Biologist', 'Chemist',
            'Psychologist', 'Psychiatrist',
            'Engineer', 'Researcher'
        ]
        
        profession = []
        
        # First check for specialty in title
        title_lower = title.lower()
        for specialty in specialties:
            if specialty.lower() in title_lower:
                profession.append(specialty)
                break
        
        # Then check for base title
        for title_key in base_titles:
            if title_key.lower() in title_lower:
                if not any(base_titles[title_key].lower() in p.lower() for p in profession):
                    profession.append(base_titles[title_key])
                break
        
        # Check description for additional context
        desc_lines = description.split('\n')[:5]  # First 5 lines
        desc_text = ' '.join(desc_lines).lower()
        
        # If no profession found in title, check description
        if not profession:
            for specialty in specialties:
                if specialty.lower() in desc_text:
                    profession.append(specialty)
                    break
            for title_key in base_titles:
                if title_key.lower() in desc_text:
                    if not any(base_titles[title_key].lower() in p.lower() for p in profession):
                        profession.append(base_titles[title_key])
                    break
        
        # Combine titles (e.g., "Brain Surgeon, Doctor")
        return ", ".join(profession) if profession else ""
    
    def _extract_organization(self, title: str, description: str) -> str:
        """Extract organization from title or description"""
        # Look for organization in parentheses
        org_match = re.search(r'\((.*?)\)', title)
        if org_match:
            return org_match.group(1)
            
        # Look for organization in description
        desc_lines = description.split('\n')[:5]
        for line in desc_lines:
            if any(x in line.lower() for x in ['university', 'institute', 'organization', 'company']):
                return line.strip()
                
        return ""