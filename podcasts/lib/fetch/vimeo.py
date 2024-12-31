import json
import logging
from typing import Dict
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..config import Config

logger = logging.getLogger(__name__)

def get_vimeo_data_headless(url: str) -> Dict:
    """Get Vimeo video data using headless browser"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        # Wait for player config to load
        wait = WebDriverWait(driver, 10)
        config_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-config-url]'))
        )
        
        config_url = config_element.get_attribute('data-config-url')
        response = requests.get(config_url)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        logger.error(f"Failed to fetch Vimeo data: {str(e)}")
        raise ValueError(f"Could not get Vimeo data: {str(e)}")
        
    finally:
        if 'driver' in locals():
            driver.quit()

def create_episode_metadata(video_id: str, data: Dict) -> Dict:
    """Create episode metadata from Vimeo data"""
    video = data['video']
    owner = video.get('owner', {})
    
    return {
        'title': video.get('title', ''),
        'description': video.get('description', ''),
        'published_at': datetime.fromtimestamp(video.get('upload_date', 0)),
        'podcast_name': owner.get('name', ''),
        'interviewee': {
            'name': _extract_interviewee_name(video.get('title', '')),
            'profession': _extract_profession(video.get('description', '')),
            'organization': _extract_organization(video.get('description', ''))
        }
    }

def _extract_interviewee_name(title: str) -> str:
    """Extract interviewee name from video title"""
    if ' - ' in title:
        parts = title.split(' - ')
        return parts[1] if len(parts) > 2 else parts[-1]
    return title

def _extract_profession(description: str) -> str:
    """Extract profession from video description"""
    prof_indicators = ['PhD', 'Dr.', 'Professor', 'CEO', 'Founder']
    for indicator in prof_indicators:
        if indicator.lower() in description.lower():
            return indicator
    return ""

def _extract_organization(description: str) -> str:
    """Extract organization from video description"""
    # Look for organization in parentheses
    if '(' in description and ')' in description:
        start = description.find('(') + 1
        end = description.find(')')
        return description[start:end]
    
    # Look for organization keywords
    for line in description.split('\n')[:5]:
        if any(x in line.lower() for x in ['university', 'institute', 'organization', 'company']):
            return line.strip()
    return ""

def process_vimeo_transcript(entry) -> Path:
    """Process Vimeo transcript"""
    try:
        data = get_vimeo_data_headless(entry.url)
        metadata = data.get('request', {}).get('files', {}).get('captions', {})
        
        if not metadata or not metadata.get('webvtt'):
            raise ValueError("No transcript available")
            
        transcript_path = Config.get_transcript_path(entry.episode_id)
        
        response = requests.get(metadata['webvtt']['url'])
        response.raise_for_status()
        vtt_content = response.text
        
        formatted_lines = ["# Transcript\n"]
        formatted_lines.append("```timestamp-transcript")
        
        # Process VTT content
        lines = vtt_content.splitlines()
        start_idx = next((i for i, line in enumerate(lines) if line.strip() == ""), 0) + 1
        
        for line in lines[start_idx:]:
            line = line.strip()
            if '-->' in line:
                formatted_lines.append(f"\n[{line}]")
            elif line and not line.isdigit():
                formatted_lines.append(line)
        
        formatted_lines.append("\n```")
        
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(formatted_lines))
        
        return transcript_path
        
    except Exception as e:
        logger.error(f"Failed to process transcript: {str(e)}")
        raise
