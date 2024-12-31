from datetime import datetime
from pathlib import Path
import re
from typing import Dict
import json

from ..config import Config

class PodcastID:
    def __init__(self, 
                 date: datetime,
                 podcast_name: str,
                 interviewee_name: str,
                 platform: str,
                 count: int = 1):
        self.date = date
        self.podcast_name = self._sanitize_name(podcast_name)
        self.interviewee_name = self._sanitize_name(interviewee_name)
        self.platform = platform.lower()
        self.count = count

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Convert name to lowercase, replace spaces with underscores, remove special chars"""
        # Remove special characters and convert to lowercase
        clean = re.sub(r'[^\w\s-]', '', name.lower())
        # Replace spaces with underscores and remove duplicate underscores
        return re.sub(r'_+', '_', clean.replace(' ', '_'))

    @property
    def base_id(self) -> str:
        """Generate the base ID string"""
        return f"{self.date.strftime('%y_%m_%d')}_{self.podcast_name}_{self.interviewee_name}_{self.platform}_{self.count:02d}"

    @classmethod
    def from_string(cls, id_string: str) -> 'PodcastID':
        """Create PodcastID instance from an existing ID string"""
        pattern = r"(\d{2}_\d{2}_\d{2})_(.+?)_(.+?)_(.+?)_(\d{2})$"
        match = re.match(pattern, id_string)
        if not match:
            raise ValueError(f"Invalid ID format: {id_string}")
        
        date_str, podcast, interviewee, platform, count = match.groups()
        date = datetime.strptime(date_str, "%y_%m_%d")
        return cls(date, podcast, interviewee, platform, int(count))

class IDGenerator:
    def __init__(self):
        self.id_cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, int]:
        """Load ID cache from podcasts.json"""
        cache = {}
        if Config.PODCAST_LIST.exists():
            with open(Config.PODCAST_LIST) as f:
                data = json.load(f)
                for entry in data:
                    # Only count entries that still exist in the file
                    key = f"{entry['podcast_name']}_{entry['interviewee']['name']}"
                    count = int(entry['episode_id'].split('_')[-1].replace('vimeo_', '').replace('youtube_', ''))
                    cache[key] = max(cache.get(key, 0), count)
        return cache
    
    def reset_cache(self):
        """Reset the ID cache"""
        self.id_cache = {}
    
    def generate_id(self, 
                   date: datetime,
                   podcast_name: str,
                   interviewee_name: str,
                   platform: str) -> PodcastID:
        """Generate a new unique ID"""
        key = f"{podcast_name}_{interviewee_name}"
        count = self.id_cache.get(key, 0) + 1
        self.id_cache[key] = count
        
        return PodcastID(date, podcast_name, interviewee_name, platform, count)