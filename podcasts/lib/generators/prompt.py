from typing import Dict, List, Optional
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_analysis_prompt(
    title: str,
    podcast_name: str,
    episode_id: str,
    share_url: str,
    transcript_filename: str,
    platform_type: str,
    date: str = None,
    interviewee: Dict = None
) -> str:
    """Generate a ChatGPT prompt for podcast analysis in Obsidian format
    
    Args:
        title: Episode title
        podcast_name: Name of podcast
        episode_id: Unique episode identifier
        share_url: URL to episode
        transcript_filename: Name of transcript file
        platform_type: Platform type (youtube/vimeo)
        date: Air date (optional)
        interviewee: Optional dictionary with interviewee details
    
    Returns:
        str: Formatted prompt text
    """
    
    # Build interviewee context
    interviewee_context = f"""  - Name: {interviewee.get('name', 'Unknown')}
  - Profession: {interviewee.get('profession', 'Unknown')}
  - Organization: {interviewee.get('organization', 'Unknown')}""" if interviewee else "  No interviewee information available"

    # Format date if provided
    date_str = date if date else datetime.now().strftime('%Y-%m-%d')

    prompt = f"""Please perform a comprehensive analysis of this podcast episode's transcript, considering its full length and complexity. Use the following details to structure your response:

### Input Details
- Title: {title}
- Show: {podcast_name}
- Episode ID: {episode_id}
- Platform: {platform_type}
- Share URL: {share_url}
- Air Date: {date_str}
- Transcript File: [[Transcripts/{transcript_filename}]]
- Known Interviewee Info:
{interviewee_context}

### Analysis Guidelines
1. Content Coverage:
   - Read and analyze the ENTIRE transcript before summarizing
   - Pay special attention to topic transitions and thematic shifts
   - Note when the conversation depth changes or pivots
   - Consider both explicit statements and implicit connections
   - Track recurring themes across the full duration

2. Time-Based Analysis:
   - Mark significant timestamps throughout the entire episode
   - Note the progression of ideas across early, middle, and late segments
   - Identify when key concepts are introduced vs. when they're expanded upon
   - Track how ideas evolate or change throughout the conversation

3. Multi-Speaker Dynamics:
   - Distinguish between host and guest perspectives
   - Note areas of agreement/disagreement
   - Capture unique insights from each participant
   - Track when viewpoints converge or diverge

4. Complex Topic Handling:
   - Break down complex topics into digestible components
   - Connect related ideas across different timestamps
   - Identify prerequisite concepts for complex topics
   - Note when technical terms are introduced and explained

5. Depth Considerations:
   - For 2+ hour episodes, ensure coverage of later segments
   - Balance early, middle, and late content representation
   - Track energy levels and content quality changes
   - Note when deep dives occur vs. surface-level discussion

6. Cross-Referencing:
   - Note mentions of other episodes, books, or resources
   - Track references to previous conversations
   - Identify potential connections to other content
   - Flag areas for future research or follow-up

### Output Structure
- **Metadata**: All input details formatted in YAML at the top for machine-readability.
- **Summary**: A concise, engaging summary of the episode (2–3 sentences).
- **Claims**: A structured list of 8–20 significant claims, each with:
  * Timestamp (HH:MM:SS format)
  * Category (key point, unique perspective, groundbreaking idea)
  * Clear, concise statement
  * Segment indicator (early, middle, late)
- **Themes and Topics**: A high-level list of themes and specific topics discussed.
- **Insights and Questions**: Notes or questions based on the episode for creative exploration.
- **Links**: Include links to the transcript, related episodes, and external resources.

## Topic Progression
- Early Segment (0:00-33%):
  - Main themes:
  - Key transitions:
- Middle Segment (33-66%):
  - Main themes:
  - Key transitions:
- Late Segment (66-100%):
  - Main themes:
  - Key transitions:

## Technical Terms & Concepts
- Term 1: [First mentioned HH:MM:SS] Brief explanation
- Term 2: [First mentioned HH:MM:SS] Brief explanation

## Deep Dives
- Topic 1: [HH:MM:SS - HH:MM:SS] Brief overview
- Topic 2: [HH:MM:SS - HH:MM:SS] Brief overview

## External References
- Books mentioned:
- People referenced:
- Related episodes:
- Recommended resources:

## Follow-up Research
- [ ] Topic 1: Specific area for deeper investigation
- [ ] Topic 2: Potential connection to explore

### Quality Assurance Checklist
1. Coverage:
   - [ ] Analyzed entire transcript
   - [ ] Balanced representation of all segments
   - [ ] Captured major theme transitions
   - [ ] Noted significant context shifts

2. Claims Quality:
   - [ ] Verified timestamps accuracy
   - [ ] Eliminated redundant claims
   - [ ] Balanced claim distribution
   - [ ] Preserved complex context

3. Technical Accuracy:
   - [ ] Verified technical terms
   - [ ] Checked name spellings
   - [ ] Validated external references
   - [ ] Confirmed chronological order

4. Cross-Linking:
   - [ ] Added relevant internal links
   - [ ] Included external references
   - [ ] Tagged appropriately
   - [ ] Noted related content

Please ensure your analysis:
- Maintains context across the entire episode length
- Balances detail with accessibility
- Preserves complex ideas while making them approachable
- Creates useful entry points for future research
- Enables effective knowledge graph connections

Output the complete Markdown note with all sections filled based on thorough analysis of the entire transcript."""

    return prompt

def update_episode_markdown(
    episode_path: Path,
    gpt_response: Dict,
    transcript_path: Path,
    claims_path: Path
) -> str:
    """Generate updated episode markdown with GPT analysis
    
    Args:
        episode_path: Path to episode markdown file
        gpt_response: Parsed JSON response from ChatGPT
        transcript_path: Path to transcript file
        claims_path: Path to claims file
        
    Returns:
        str: Updated markdown content
    """
    
    # Convert paths to relative for Obsidian linking
    transcript_link = f"[[{transcript_path.name}]]"
    claims_link = f"[[{claims_path.name}]]"
    
    # Format interviewee section
    interviewee = gpt_response["interviewee"]
    interviewee_md = f"""## Interviewee
- **Name**: {interviewee['name']}
- **Profession**: {interviewee['profession']}
- **Organization**: {interviewee['organization']}
"""

    # Format summary
    summary_md = f"""## Summary
{gpt_response['summary']}
"""

    # Format related content
    related_md = f"""## Related Content
- Transcript: {transcript_link}
- Claims Analysis: {claims_link}
"""

    # Format metadata
    metadata_md = f"""## Metadata
### Topics
{', '.join(gpt_response['related_topics'])}

### Tags
{' '.join(['#' + tag for tag in gpt_response['tags']])}
"""

    # Combine sections
    markdown = f"""# {episode_path.stem}

{interviewee_md}

{summary_md}

{related_md}

{metadata_md}
"""

    return markdown

def format_claims_markdown(gpt_response: Dict) -> str:
    """Format claims analysis as markdown
    
    Args:
        gpt_response: Parsed JSON response from ChatGPT
        
    Returns:
        str: Formatted markdown for claims file
    """
    
    claims_md = ["# Claims Analysis\n"]
    
    # Group claims by filter type
    claims_by_filter = {}
    for claim in gpt_response["claims"]:
        filter_type = claim["filter"]
        if filter_type not in claims_by_filter:
            claims_by_filter[filter_type] = []
        claims_by_filter[filter_type].append(claim)
    
    # Format each section
    for filter_type, claims in claims_by_filter.items():
        claims_md.append(f"\n## {filter_type.title()}\n")
        for claim in claims:
            claims_md.append(f"### Claim {claim['claim_id']} ({claim['timestamp']})")
            claims_md.append(claim["claim"])
            claims_md.append(f"*Segment: {claim['segment']}*\n")
    
    return "\n".join(claims_md)

def save_prompt_to_episode(episode_path: Path, prompt: str):
    """Temporarily save the ChatGPT prompt to the episode file
    
    Args:
        episode_path: Path to episode markdown file
        prompt: Generated prompt text
    """
    with open(episode_path, 'a') as f:
        f.write("\n\n## ChatGPT Analysis Prompt\n")
        f.write("```\n")
        f.write(prompt)
        f.write("\n```\n") 