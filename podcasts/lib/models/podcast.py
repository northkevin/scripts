from typing import Dict, List
from pathlib import Path
import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict

from ..config import Config
from ..generators.id import IDGenerator

logger = logging.getLogger(__name__)

@dataclass
class Interviewee:
    name: str
    profession: str = ""
    organization: str = ""

@dataclass
class PodcastEntry:
    episode_id: str
    url: str
    platform: str
    title: str
    description: str
    published_at: datetime
    podcast_name: str
    interviewee: Interviewee
    status: str = "pending"
    episodes_file: str = ""
    claims_file: str = ""
    transcripts_file: str = ""
    
    @property
    def process_command(self) -> str:
        return f"python -m podcasts process-podcast --episode_id {self.episode_id}"

class PodcastList:
    def __init__(self):
        self.entries: List[PodcastEntry] = []
        self._load()
    
    def _load(self):
        """Load podcast list from file"""
        try:
            if Config.PODCAST_LIST.exists():
                with open(Config.PODCAST_LIST, 'r') as f:
                    data = json.load(f)
                    
                self.entries = [
                    PodcastEntry(
                        **{
                            **entry,
                            'published_at': datetime.fromisoformat(entry['published_at']),
                            'interviewee': Interviewee(**entry['interviewee'])
                        }
                    )
                    for entry in data
                ]
                
        except Exception as e:
            logger.error(f"Failed to load podcast list: {e}")
            self.entries = []
    
    def _save(self):
        """Save podcast list to file"""
        try:
            data = [
                {
                    **asdict(entry),
                    'published_at': entry.published_at.isoformat()
                }
                for entry in self.entries
            ]
            
            with open(Config.PODCAST_LIST, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save podcast list: {e}")
    
    def add_entry(self, url: str, platform: str, metadata: Dict, existing_id: str = None) -> PodcastEntry:
        """Add new podcast entry"""
        # Generate or reuse episode ID
        if existing_id:
            episode_id = existing_id
        else:
            episode_id = IDGenerator().generate_id(platform, metadata['published_at'])
        
        # Create entry
        entry = PodcastEntry(
            episode_id=episode_id,
            url=url,
            platform=platform,
            title=metadata['title'],
            description=metadata['description'],
            published_at=metadata['published_at'],
            podcast_name=metadata['podcast_name'],
            interviewee=Interviewee(**metadata['interviewee'])
        )
        
        self.entries.append(entry)
        self._save()
        
        return entry
    
    def get_entry(self, episode_id: str) -> PodcastEntry:
        """Get podcast entry by ID"""
        return next(
            (entry for entry in self.entries if entry.episode_id == episode_id),
            None
        )
    
    def update_entry(self, episode_id: str, **kwargs):
        """Update podcast entry"""
        entry = self.get_entry(episode_id)
        if entry:
            for key, value in kwargs.items():
                setattr(entry, key, value)
            self._save()

def save_state(episode_id: str, status: str = "processing", error: str = None):
    """Save podcast processing state"""
    podcast_list = PodcastList()
    entry = podcast_list.get_entry(episode_id)
    
    if entry:
        entry.status = status
        podcast_list._save()
        
        if error:
            logger.error(f"Error processing {episode_id}: {error}")