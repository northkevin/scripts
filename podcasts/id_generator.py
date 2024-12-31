from datetime import datetime
from pathlib import Path
import re
from typing import Optional, Dict
import json

from config import Config

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

    def get_filename(self, file_type: str) -> str:
        """Generate filename for different file types"""
        return f"{self.base_id}_{file_type}.md"

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
    def __init__(self, database_path: Path = Config.DATABASE):
        self.database_path = database_path
        self.id_cache = self._load_id_cache()

    def _load_id_cache(self) -> Dict[str, int]:
        """Load existing IDs to track counts"""
        if not self.database_path.exists():
            return {}
            
        with open(self.database_path) as f:
            episodes = json.load(f)
            
        cache = {}
        for episode in episodes:
            if 'podcast_name' in episode and 'interviewee' in episode:
                key = f"{episode['podcast_name']}_{episode['interviewee']['name']}"
                count = cache.get(key, 0) + 1
                cache[key] = count
        return cache

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

    def get_filenames(self, podcast_id: PodcastID) -> Dict[str, Path]:
        """Get all related filenames for a podcast ID"""
        return {
            'episode': Config.EPISODES_DIR / podcast_id.get_filename('episode'),
            'transcript': Config.TRANSCRIPTS_DIR / podcast_id.get_filename('transcript'),
            'claims': Config.CLAIMS_DIR / podcast_id.get_filename('claims')
        }

# Example usage:
"""
generator = IDGenerator()

# Generate new ID
podcast_id = generator.generate_id(
    date=datetime(2024, 9, 24),
    podcast_name="Danny Jones",
    interviewee_name="Jack Kruse",
    platform="youtube"
)

# Get all related filenames
filenames = generator.get_filenames(podcast_id)
print(f"Episode file: {filenames['episode']}")
print(f"Transcript file: {filenames['transcript']}")
print(f"Claims file: {filenames['claims']}")

# Parse existing ID
existing_id = PodcastID.from_string("24_09_24_danny_jones_jack_kruse_youtube_01")
""" 