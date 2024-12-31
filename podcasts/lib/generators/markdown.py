from pathlib import Path
import logging

from ..config import Config
from ..models.podcast import PodcastEntry
from .prompt import generate_analysis_prompt, save_prompt_to_episode

logger = logging.getLogger(__name__)

class MarkdownGenerator:
    def generate_episode_markdown(self, entry: PodcastEntry) -> Path:
        """Generate initial episode markdown with analysis prompt"""
        
        # Create episode file
        episode_file = Config.EPISODES_DIR / f"{entry.episode_id}.md"
        
        # Format transcript link using config
        transcript_link = (
            f"[[{entry.episode_id}_transcript{Config.TRANSCRIPT_FILE_EXT}]]" 
            if entry.transcripts_file else "Transcript not available"
        )
        
        # Generate initial content with YAML frontmatter and essential metadata only
        content = f"""---
title: "{entry.title}"
show: "{entry.podcast_name}"
episode_id: "{entry.episode_id}"
platform: "{entry.platform}"
url: "{entry.url}"
status: "pending_analysis"
type: "podcast_episode"
---

# {entry.title}

## Episode Information
- **Show**: {entry.podcast_name}
- **Platform**: {entry.platform}
- **URL**: {entry.url}
- **Transcript**: {transcript_link}

## Interviewee
- **Name**: {entry.interviewee.name}
- **Profession**: {entry.interviewee.profession}
- **Organization**: {entry.interviewee.organization}

"""
        
        # Save initial content
        with open(episode_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Generate and append ChatGPT prompt
        prompt = generate_analysis_prompt(
            title=entry.title,
            podcast_name=entry.podcast_name,
            episode_id=entry.episode_id,
            share_url=entry.url,
            transcript_filename=f"{entry.episode_id}_transcript.md",
            platform_type=entry.platform,
            interviewee={
                "name": entry.interviewee.name,
                "profession": entry.interviewee.profession,
                "organization": entry.interviewee.organization
            }
        )
        
        save_prompt_to_episode(episode_file, prompt)
        
        return episode_file
    