# scripts/podcasts/transcript_utils.py

import requests
import logging
from pathlib import Path
from config import Config

logger = logging.getLogger("podcast_cli")

def download_vtt_file(webvtt_link: str, output_path: str):
    """
    Downloads the .vtt file from 'webvtt_link' and saves as 'output_path'.
    """
    # Convert string path to Path object
    output_path = Path(output_path)
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading .vtt from {webvtt_link} to {output_path}")
    
    resp = requests.get(webvtt_link, timeout=30)
    resp.raise_for_status()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(resp.text)

    logger.info(f"Saved VTT file => {output_path}")

def get_transcript_path(episode_id: str, platform_type: str = None) -> Path:
    """Get the appropriate transcript path based on platform"""
    transcript_dir = Config.get_transcript_dir(platform_type)
    return transcript_dir / f"{episode_id}_transcript.vtt"