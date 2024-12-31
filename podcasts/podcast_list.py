from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Optional, List
import re
from dataclasses import dataclass, asdict

from id_generator import PodcastID, IDGenerator
from config import Config

@dataclass
class Interviewee:
    name: str
    profession: str = ""
    organization: str = ""

@dataclass
class PodcastEntry:
    url: str
    platform: str
    title: str
    podcast_name: str
    interviewee: Interviewee
    episode_id: str
    date: str
    status: str = "pending"  # pending, processing, error, complete
    episodes_file: str = ""
    claims_file: str = ""
    transcripts_file: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def is_complete(self) -> bool:
        """Check if all required files are present"""
        return all([
            self.episodes_file,
            self.claims_file,
            self.transcripts_file
        ])

class PodcastList:
    def __init__(self, file_path: Path = Config.PODCAST_LIST):
        self.file_path = file_path
        self.entries: List[PodcastEntry] = []
        self._load()
    
    def _load(self):
        """Load existing podcast list"""
        if self.file_path.exists():
            with open(self.file_path) as f:
                data = json.load(f)
                self.entries = [
                    PodcastEntry(**{**entry, "interviewee": Interviewee(**entry["interviewee"])})
                    for entry in data
                ]
    
    def _save(self):
        """Save podcast list to file"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, 'w') as f:
            json.dump([entry.to_dict() for entry in self.entries], f, indent=2)
    
    def add_entry(self, url: str, platform: str, metadata: Dict) -> PodcastEntry:
        """Add new podcast entry"""
        # Check if URL already exists
        if any(entry.url == url for entry in self.entries):
            raise ValueError(f"URL already exists in podcast list: {url}")
        
        # Extract date from metadata
        date = datetime.strptime(metadata['air_date'].split('T')[0], '%Y-%m-%d')
        
        # Create interviewee info
        interviewee = Interviewee(
            name=metadata['interviewee']['name'],
            profession=metadata['interviewee'].get('profession', ''),
            organization=metadata['interviewee'].get('organization', '')
        )
        
        # Generate unique ID
        id_generator = IDGenerator()
        podcast_id = id_generator.generate_id(
            date=date,
            podcast_name=metadata['podcast_name'],
            interviewee_name=interviewee.name,
            platform=platform
        )
        
        # Create entry
        entry = PodcastEntry(
            url=url,
            platform=platform,
            title=metadata['title'],
            podcast_name=metadata['podcast_name'],
            interviewee=interviewee,
            episode_id=podcast_id.base_id,
            date=date.strftime('%Y-%m-%d')
        )
        
        self.entries.append(entry)
        self._save()
        return entry
    
    def get_entry(self, episode_id: str) -> Optional[PodcastEntry]:
        """Get entry by episode ID"""
        return next((entry for entry in self.entries if entry.episode_id == episode_id), None)
    
    def update_entry(self, episode_id: str, **kwargs) -> Optional[PodcastEntry]:
        """Update entry fields"""
        entry = self.get_entry(episode_id)
        if entry:
            for key, value in kwargs.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            
            # Auto-update status if all files are present
            if entry.is_complete():
                entry.status = "complete"
            
            self._save()
        return entry

def save_state(episode_id: str, status: str = "processing", **kwargs):
    """Save current episode state"""
    state = {
        "episode_id": episode_id,
        "status": status,
        **kwargs
    }
    
    with open(Config.CURRENT_STATE, 'w') as f:
        json.dump(state, f, indent=2)

def get_state() -> Dict:
    """Get current episode state"""
    if Config.CURRENT_STATE.exists():
        with open(Config.CURRENT_STATE) as f:
            return json.load(f)
    return {}