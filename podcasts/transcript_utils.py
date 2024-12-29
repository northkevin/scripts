# scripts/podcasts/transcript_utils.py

import requests
import logging

logger = logging.getLogger("podcast_cli")

def download_vtt_file(webvtt_link: str, output_path: str):
    """
    Downloads the .vtt file from 'webvtt_link' and saves as 'output_path'.
    """
    logger.info(f"Downloading .vtt from {webvtt_link} to {output_path}")
    
    resp = requests.get(webvtt_link, timeout=30)
    resp.raise_for_status()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(resp.text)

    logger.info(f"Saved VTT file => {output_path}")