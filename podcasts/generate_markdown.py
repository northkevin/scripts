from pathlib import Path
from typing import Dict, Optional
import json
from datetime import datetime

from config import Config

class MarkdownGenerator:
    def __init__(self):
        self.obsidian_vault_path = Config.OBSIDIAN_VAULT

    def generate_episode_markdown(self, entry) -> str:
        """Generate episode markdown content"""
        # Convert tags to Obsidian format if they exist
        tags = []
        related_topics = []
        
        if hasattr(entry, 'tags'):
            tags = [f"#{tag.replace(' ', '_')}" for tag in entry.tags]
        if hasattr(entry, 'related_topics'):
            related_topics = [f"#{topic.replace(' ', '_')}" for topic in entry.related_topics]
        
        markdown = f"""# {entry.title}

## Metadata
- **Date**: {entry.date}
- **Podcast**: {entry.podcast_name}
- **Platform**: {entry.platform}
- **URL**: {entry.url}

## Interviewee
- **Name**: {entry.interviewee.name}
- **Profession**: {entry.interviewee.profession}
- **Organization**: {entry.interviewee.organization}

## Summary
{getattr(entry, 'summary', 'No summary available.')}

## Tags
{', '.join(tags)}

## Related Topics
{', '.join(related_topics)}

## Transcript
{self._get_transcript_link(entry)}

## Notes
"""
        return markdown

    def generate_claims_markdown(self, entry) -> str:
        """Generate claims markdown content"""
        markdown = f"""# Claims | {entry.title}

## Podcast Info
- **Date**: {entry.date}
- **Podcast**: {entry.podcast_name}
- **Guest**: {entry.interviewee.name}

## Key Claims
- 

## Evidence Presented
- 

## Questions/Concerns
- 

## Follow-up Research
- 

## Related Episodes
- 

## Tags
#claims
"""
        return markdown

    def _get_transcript_link(self, entry) -> str:
        """Generate Obsidian link to transcript file if available"""
        if entry.transcripts_file:
            file_path = Path(entry.transcripts_file)
            return f"[[{file_path.stem}|View Transcript]]"
        return "No transcript available."

    def save_markdown(self, podcast_id: str, markdown_content: str, file_type: str) -> Path:
        """Save markdown content to appropriate directory"""
        if file_type == 'episode':
            output_dir = Config.EPISODES_DIR
        elif file_type == 'claims':
            output_dir = Config.CLAIMS_DIR
        else:
            raise ValueError(f"Unknown file type: {file_type}")

        output_path = output_dir / f"{podcast_id}_{file_type}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding='utf-8') as f:
            f.write(markdown_content)
            
        return output_path
