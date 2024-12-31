from pathlib import Path
import os

class Config:
    # Base directories
    BASE_DIR = Path(__file__).parent
    PROJECT_ROOT = BASE_DIR.parent
    
    # Obsidian configuration
    OBSIDIAN_VAULT = Path(os.getenv('OBSIDIAN_VAULT_PATH', '/Users/kevinnorth/Documents/Obsidian Vault'))
    
    # Main data files
    PODCAST_LIST = BASE_DIR / "podcasts.json"  # Current location
    # Future Obsidian location could be:
    # PODCAST_LIST = OBSIDIAN_VAULT / "Podcasts" / "podcasts.json"
    
    # Data directories
    DATA_DIR = BASE_DIR / "Podcast Data"
    VIMEO_DIR = DATA_DIR / "vimeo"
    YOUTUBE_DIR = DATA_DIR / "youtube"
    
    # Content-specific directories
    EPISODES_DIR = DATA_DIR / "Episodes"
    CLAIMS_DIR = DATA_DIR / "Claims"
    TRANSCRIPTS_DIR = DATA_DIR / "Transcripts"
    
    # Platform-specific transcript directories
    VIMEO_TRANSCRIPTS = VIMEO_DIR / "transcripts"
    YOUTUBE_TRANSCRIPTS = YOUTUBE_DIR / "transcripts"
    
    # State files
    CURRENT_STATE = DATA_DIR / ".current_episode.json"
    
    # Database
    DATABASE = DATA_DIR / "podcast_data.json"
    
    @classmethod
    def ensure_dirs(cls):
        """Create all necessary directories"""
        dirs = [
            cls.DATA_DIR,
            cls.VIMEO_DIR,
            cls.YOUTUBE_DIR,
            cls.EPISODES_DIR,
            cls.CLAIMS_DIR,
            cls.TRANSCRIPTS_DIR,
            cls.VIMEO_TRANSCRIPTS,
            cls.YOUTUBE_TRANSCRIPTS,
        ]
        for dir in dirs:
            if not dir.exists():
                dir.mkdir(parents=True)
                print(f"Created directory: {dir}")
    
    @classmethod
    def get_transcript_dir(cls, platform_type: str) -> Path:
        """Get the appropriate transcript directory based on platform"""
        if platform_type == "youtube":
            return cls.YOUTUBE_TRANSCRIPTS
        elif platform_type == "vimeo":
            return cls.VIMEO_TRANSCRIPTS
        else:
            return cls.TRANSCRIPTS_DIR

    @classmethod
    def migrate_to_obsidian(cls):
        """
        Future method to migrate podcasts.json to Obsidian vault
        """
        obsidian_podcast_dir = cls.OBSIDIAN_VAULT / "Podcasts"
        obsidian_podcast_dir.mkdir(parents=True, exist_ok=True)
        
        # TODO: Implement migration logic
        pass

# Create directories when module is imported
Config.ensure_dirs() 