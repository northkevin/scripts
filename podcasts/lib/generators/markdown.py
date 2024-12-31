from pathlib import Path
import logging

from ..config import Config

logger = logging.getLogger(__name__)

class MarkdownGenerator:
    def __init__(self):
        self.episodes_dir = Config.EPISODES_DIR
        self.claims_dir = Config.CLAIMS_DIR
    
    def generate_episode_markdown(self, entry) -> Path:
        """Generate episode markdown file"""
        output_path = self.episodes_dir / f"{entry.episode_id}.md"
        
        content = [
            f"# {entry.title}\n",
            f"## Metadata\n",
            f"- **Episode ID**: {entry.episode_id}",
            f"- **Podcast**: {entry.podcast_name}",
            f"- **Platform**: {entry.platform}",
            f"- **URL**: {entry.url}",
            f"- **Interviewee**: {entry.interviewee.name}",
            f"\n## Summary\n",
            f"{entry.summary if hasattr(entry, 'summary') else 'No summary available.'}\n",
            f"## Topics\n",
        ]
        
        if hasattr(entry, 'related_topics') and entry.related_topics:
            for topic in entry.related_topics:
                content.append(f"- {topic}")
        else:
            content.append("- No topics available")
            
        content.append("\n## Claims\n")
        content.append(f"![[{entry.episode_id}_claims]]\n")
        
        content.append("\n## Transcript\n")
        content.append(f"![[{entry.episode_id}_transcript]]\n")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
            
        return output_path
    
    def generate_claims_markdown(self, entry) -> Path:
        """Generate claims markdown file"""
        output_path = self.claims_dir / f"{entry.episode_id}_claims.md"
        
        content = [
            f"# Claims from {entry.title}\n",
            "## Key Claims\n",
            "- [ ] Add key claims here\n",
            "\n## Supporting Evidence\n",
            "- [ ] Add supporting evidence here\n"
        ]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
            
        return output_path