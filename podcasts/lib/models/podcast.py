from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict

from ..config import Config
from ..generators.id import PodcastID, IDGenerator

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
    webvtt_link: str = ""
    process_command: str = ""
    added_at: str = ""  # ISO format timestamp
    updated_at: str = ""  # ISO format timestamp
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def is_complete(self) -> bool:
        """Check if all required files are present"""
        return all([
            self.episodes_file,
            self.claims_file,
            self.transcripts_file
        ])
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow().isoformat()

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
    
    def add_entry(self, url: str, platform: str, metadata: Dict, existing_id: str = None) -> PodcastEntry:
        """Add new podcast entry"""
        current_time = datetime.utcnow().isoformat()
        
        # Extract date from metadata (should be ISO format for both platforms)
        if 'published_at' not in metadata:
            raise ValueError("Missing required field: published_at")
        
        try:
            # Handle ISO format date strings
            date = datetime.fromisoformat(metadata['published_at'].replace('Z', '+00:00'))
        except ValueError as e:
            raise ValueError(f"Invalid date format in published_at: {metadata['published_at']}") from e
        
        # Create interviewee info - handle missing fields
        interviewee_data = metadata.get('interviewee', {})
        if isinstance(interviewee_data, str):
            # If only name is provided
            interviewee = Interviewee(name=interviewee_data)
        else:
            # Full interviewee object
            interviewee = Interviewee(
                name=interviewee_data.get('name', 'Unknown'),
                profession=interviewee_data.get('profession', ''),
                organization=interviewee_data.get('organization', '')
            )
        
        # Use existing ID if provided, otherwise generate new one
        if existing_id:
            episode_id = existing_id
        else:
            # Generate unique ID
            id_generator = IDGenerator()
            podcast_id = id_generator.generate_id(
                date=date,
                podcast_name=metadata.get('podcast_name', 'Unknown Podcast'),
                interviewee_name=interviewee.name,
                platform=platform
            )
            episode_id = podcast_id.base_id
        
        # Create entry
        entry = PodcastEntry(
            url=url,
            platform=platform,
            title=metadata.get('title', 'Untitled'),
            podcast_name=metadata.get('podcast_name', 'Unknown Podcast'),
            interviewee=interviewee,
            episode_id=episode_id,
            date=date.strftime('%Y-%m-%d'),
            webvtt_link=metadata.get('webvtt_link', ''),
            process_command=f"python main.py process-podcast --episode_id {episode_id}",
            added_at=current_time,  # Set initial added_at
            updated_at=current_time  # Set initial updated_at
        )
        
        self.entries.append(entry)
        self._save()
        return entry
    
    def get_entry(self, episode_id: str) -> Optional[PodcastEntry]:
        """Get entry by episode ID"""
        return next((entry for entry in self.entries if entry.episode_id == episode_id), None)
    
    def update_entry(self, episode_id: str, **kwargs) -> None:
        """Update an existing entry"""
        entry = self.get_entry(episode_id)
        if not entry:
            raise ValueError(f"No entry found with episode_id: {episode_id}")
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        
        # Update timestamp
        entry.update_timestamp()
        
        self._save()

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