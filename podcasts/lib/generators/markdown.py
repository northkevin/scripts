from pathlib import Path
import logging

from ..config import Config
from ..models.podcast import PodcastEntry
from .prompt import generate_analysis_prompt, save_prompt_to_episode

logger = logging.getLogger(__name__)

class MarkdownGenerator:
    def generate_episode_markdown(self, entry: PodcastEntry) -> Path:
        """Generate initial episode markdown with analysis prompt"""
        
        # Create basic episode file
        episode_file = Config.EPISODES_DIR / f"{entry.episode_id}.md"
        
        # Generate initial content
        content = f"""# {entry.title}

## Episode Details
- **Show**: {entry.podcast_name}
- **Platform**: {entry.platform}
- **URL**: {entry.url}

## Interviewee
- **Name**: {entry.interviewee.name}
- **Profession**: {entry.interviewee.profession}
- **Organization**: {entry.interviewee.organization}
"""
        
        # Save initial content
        with open(episode_file, 'w') as f:
            f.write(content)
            
        # Generate and append ChatGPT prompt
        prompt = generate_analysis_prompt(
            title=entry.title,
            podcast_name=entry.podcast_name,
            share_url=entry.url,
            transcript_filename=Path(entry.transcripts_file).name if entry.transcripts_file else "",
            platform_type=entry.platform,
            interviewee={
                "name": entry.interviewee.name,
                "profession": entry.interviewee.profession,
                "organization": entry.interviewee.organization
            }
        )
        
        save_prompt_to_episode(episode_file, prompt)
        
        return episode_file
    
    def generate_claims_markdown(self, entry: PodcastEntry) -> Path:
        """Generate claims markdown file"""
        output_path = Config.CLAIMS_DIR / f"{entry.episode_id}_claims.md"
        
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