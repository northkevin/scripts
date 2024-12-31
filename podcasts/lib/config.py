from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

class Config:
    # Base directories
    BASE_DIR = Path(__file__).parent.parent
    PROJECT_ROOT = BASE_DIR
    
    # Dist directory for all generated/temporary files
    DIST_DIR = PROJECT_ROOT / "dist"
    
    # Config and state files
    CONFIG_DIR = DIST_DIR / "config"
    PODCAST_LIST = CONFIG_DIR / "podcasts.json"
    CURRENT_STATE = CONFIG_DIR / ".current_episode.json"
    
    # Obsidian configuration - simplified path
    OBSIDIAN_VAULT = Path(os.getenv('OBSIDIAN_VAULT_PATH', '/Users/kevinnorth/Documents/Podcasts'))
    OBSIDIAN_PODCASTS = OBSIDIAN_VAULT
    
    # Content directories (in Obsidian)
    EPISODES_DIR = OBSIDIAN_PODCASTS / "Episodes"
    CLAIMS_DIR = OBSIDIAN_PODCASTS / "Claims"
    TRANSCRIPTS_DIR = OBSIDIAN_PODCASTS / "Transcripts"
    
    @classmethod
    def ensure_dirs(cls):
        """Create all necessary directories"""
        # Dist directories
        dist_dirs = [
            cls.DIST_DIR,
            cls.CONFIG_DIR,
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