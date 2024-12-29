from pathlib import Path
import os

class Config:
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "Podcast Data"
    TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
    
    # Optional OpenAI integration
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")
    
    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.TRANSCRIPTS_DIR.mkdir(exist_ok=True) 