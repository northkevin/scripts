from pathlib import Path
import os

class Config:
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "Podcast Data"
    
    # Platform-specific directories and state files
    VIMEO_DIR = DATA_DIR / "vimeo"
    VIMEO_STATE = DATA_DIR / ".current_episode.vimeo.json"
    VIMEO_TRANSCRIPTS = VIMEO_DIR / "transcripts"
    
    YOUTUBE_DIR = DATA_DIR / "youtube"
    YOUTUBE_STATE = DATA_DIR / ".current_episode.youtube.json"
    YOUTUBE_TRANSCRIPTS = YOUTUBE_DIR / "transcripts"
    
    # Common files
    DATABASE = DATA_DIR / "podcast_data.json"
    
    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories"""
        for dir in [cls.VIMEO_DIR, cls.YOUTUBE_DIR, 
                   cls.VIMEO_TRANSCRIPTS, cls.YOUTUBE_TRANSCRIPTS]:
            dir.mkdir(parents=True, exist_ok=True) 