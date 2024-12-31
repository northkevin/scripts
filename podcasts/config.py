from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

class Config:
    # Base directories
    BASE_DIR = Path(__file__).parent
    PROJECT_ROOT = BASE_DIR.parent
    
    # Dist directory for all generated/temporary files
    DIST_DIR = PROJECT_ROOT / "dist"
    
    # Config and state files
    CONFIG_DIR = DIST_DIR / "config"
    PODCAST_LIST = CONFIG_DIR / "podcasts.json"
    CURRENT_STATE = CONFIG_DIR / ".current_episode.json"
    
    # Obsidian configuration
    OBSIDIAN_VAULT = Path(os.getenv('OBSIDIAN_VAULT_PATH', '/Users/kevinnorth/Documents/Obsidian Vault'))
    OBSIDIAN_PODCASTS = OBSIDIAN_VAULT / "Podcasts"
    
    # Content directories (in Obsidian)
    EPISODES_DIR = OBSIDIAN_PODCASTS / "Episodes"
    CLAIMS_DIR = OBSIDIAN_PODCASTS / "Claims"
    TRANSCRIPTS_DIR = OBSIDIAN_PODCASTS / "Transcripts"
    
    # Working directories (in dist)
    CACHE_DIR = DIST_DIR / "cache"
    VIMEO_DIR = CACHE_DIR / "vimeo"
    YOUTUBE_DIR = CACHE_DIR / "youtube"
    
    @classmethod
    def ensure_dirs(cls):
        """Create all necessary directories"""
        # Dist directories
        dist_dirs = [
            cls.DIST_DIR,
            cls.CONFIG_DIR,
            cls.CACHE_DIR,
            cls.VIMEO_DIR,
            cls.YOUTUBE_DIR,
        ]
        
        # Obsidian directories
        obsidian_dirs = [
            cls.OBSIDIAN_PODCASTS,
            cls.EPISODES_DIR,
            cls.CLAIMS_DIR,
            cls.TRANSCRIPTS_DIR,
        ]
        
        # Create all directories
        for dir_list in [dist_dirs, obsidian_dirs]:
            for dir in dir_list:
                if not dir.exists():
                    dir.mkdir(parents=True)
                    logger.debug(f"Created directory: {dir}")

# Create directories when module is imported
Config.ensure_dirs() 