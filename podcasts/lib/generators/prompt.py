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
    """Generate a ChatGPT prompt for podcast analysis in Obsidian format"""
    
    prompt = f"""Please analyze this podcast episode's transcript and generate a replacement section for the episode note in Obsidian. Focus on extracting key insights while maintaining readability and linkability.

### Input Details
- Title: {title}
- Show: {podcast_name}
- Episode ID: {episode_id}
- Platform: {platform_type}
- Share URL: {share_url}
- Transcript: [[{transcript_filename}]]

### Analysis Instructions
1. Notable Quotes (HIGHEST PRIORITY):
   - Select 2-3 powerful quotes that:
     * Capture the most paradigm-shifting moment
     * Represent the emotional peak of the conversation
     * Showcase the most controversial or thought-provoking insight
     * Serve as a "hook" for the entire episode
     * Make the reader want to listen immediately
   - Format quotes to:
     * Include speaker emotion/tone where relevant
     * Provide minimal but crucial context
     * Highlight the most impactful moments
     * Draw attention to unique perspectives

2. Episode Overview Requirements:
   - Provide a 1-2 sentence summary that captures:
     * The core topic or main thesis
     * The unique perspective or approach
     * The broader implications or significance
     * The key areas of discussion
   - Avoid generic descriptions
   - Include specific subject matter
   - Name key concepts introduced
   - Highlight what makes this episode distinctive

3. Claims Analysis (CRITICAL):
   - Extract 8-15 significant claims - this is essential for cross-linking across episodes
   - Each claim should represent a distinct, substantial insight
   - Claims form the foundation for knowledge graph connections
   - Avoid redundant or superficial points
   - Look for:
     * Paradigm-shifting statements
     * Novel interpretations of familiar concepts
     * Unique perspectives that challenge conventional wisdom
     * Interconnections with other fields or topics
     * Technical insights and their broader implications
   - Claims will be used to:
     * Build topic networks across episodes
     * Connect ideas between different speakers
     * Identify emerging patterns and themes
     * Enable deep comparative analysis
     * In-depth explorations of complex topics
     * Detailed technical discussions

4. Content Coverage:
   - Analyze the ENTIRE transcript before summarizing
   - Track topic transitions and thematic shifts
   - Note conversation depth changes and pivots
   - Consider both explicit statements and implicit connections
   - Balance early, middle, and late segment representation

5. Multi-Speaker Dynamics:
   - Distinguish between host and guest perspectives
   - Note areas of agreement/disagreement
   - Capture unique insights from each participant
   - Track viewpoint convergence/divergence

6. Complex Topic Handling:
   - Break down complex topics into digestible components
   - Connect related ideas across different timestamps
   - Identify prerequisite concepts
   - Note when technical terms are introduced

7. Obsidian Formatting:
   - Use #tags for topics, themes, and key concepts
   - Use [[links]] only for existing documents
   - Use **bold** for emphasis and important terms
   - Use > [!quote] for significant quotes
   - Use proper heading hierarchy
   - Use 4 spaces for each level of indentation
   - Ensure consistent spacing after list markers (- or 1.)
   - Start each new list item at the correct indentation level
   

<start-section>
## Notable Quotes
> [!quote] [Speaker Name]
> "The most paradigm-shifting statement"
> - Context: [Brief emotional/intellectual impact]
> #paradigm-shift #key-insight

## Episode Overview
[Generate 1-2 sentences that capture the episode's essence, key topics, and significance]

## Key Claims
8-15 most significant insights that contribute to our broader knowledge network:

1. **Core Insight**: Claim text
   - Speaker perspective
   - Supporting context
   - Related: #tag
   - Type: #key-point #unique-perspective #groundbreaking
   - Segment: Early/Middle/Late

## Conversation Flow
**Opening** 
- Core themes: [Main topics introduced]
- Key transitions: [How discussion evolves]
- Notable insights: [Key points from first third]
#early-segment

**Development**
- Evolution: [How topics deepen]
- Key shifts: [Major perspective changes]
- Main developments: [Critical middle points]
#middle-segment

**Conclusion**
- Resolution: [How topics conclude]
- Final insights: [Key revelations]
- Key takeaways: [Essential lessons]
#late-segment

## Technical Terms & Concepts
- **[Term]**
  - Definition/Context
  - Evolution throughout discussion
  - Related: #tag
  #technical-term

## External References
**Books & Publications**
- **[Book Title]** by [Author Name]
  - Context: [How this book relates to discussion]
  - Connection: [Link to main themes]
  #book #author-[name] #[relevant-topic] #[century-published]

**People & Organizations**
- **[Person Name]** - [Role/Position]
  - Contribution: [Their specific insight or impact]
  - Field: [Area of expertise/influence]
  #person #[role] #[field] #[century-active]

**Technologies & Methods**
- **[Technology/Method Name]**
  - Description: [What it is/does]
  - Significance: [Why it matters to discussion]
  #technology #[type] #[application] #[century-developed]

## Research Threads
- [ ] **Topic** - Specific area to explore
- [ ] **Connection** - Potential link to investigate

## Tags
#podcast #{platform_type} #episode-topic #key-themes
<end-section>

Remember:
1. Maintain comprehensive coverage while being concise
2. Preserve speaker dynamics and perspective shifts
3. Track idea evolution across the full episode
4. Break down complex topics effectively
5. Create meaningful connections through tags
6. Ensure proper linking to transcript
7. Balance detail with accessibility
8. Create useful entry points for future research

IMPORTANT: 
- Include ONLY the markdown content between <start-section> and <end-section> tags, but DO NOT include these tags
- Your response should start directly with '## Key Claims' and end with the tags section."""

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
    """Save the ChatGPT analysis section and prompt in the episode file
    
    Args:
        episode_path: Path to episode markdown file
        prompt: Generated prompt text
    """
    with open(episode_path, 'a') as f:
        # Add Analysis section first
        f.write("\n\n---\n")
        f.write("## ChatGPT Analysis\n\n")
        f.write("> [!note] Paste the ChatGPT response below this line\n\n")
        f.write("...paste here...\n\n")
        f.write("\n\n---\n\n")
        
        
        
        # Add Prompt section below
        f.write("## ChatGPT Prompt\n\n")
        f.write("> [!info] Use this prompt with the transcript to generate the analysis above\n\n")
        f.write("```\n")
        f.write(prompt)
        f.write("\n```\n")
        f.write("\n---\n") 