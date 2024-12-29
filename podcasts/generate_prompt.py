import json
import os

def load_json_data(json_file_path):
    """
    Load the JSON data from the specified file.

    Args:
        json_file_path (str): Path to the JSON file.

    Returns:
        list: A list of JSON objects (episodes).
    """
    with open(json_file_path, "r") as file:
        return json.load(file)

def find_episode_by_id(json_file_path, episode_id):
    """
    Find the episode with the given ID in the JSON file.

    Args:
        json_file_path (str): Path to the JSON file.
        episode_id (str): The episode ID to search for.

    Returns:
        dict: The episode JSON object if found, else None.
    """
    episodes = load_json_data(json_file_path)
    return next((ep for ep in episodes if ep.get("episode_id") == episode_id), None)

def generate_prompt(episode_id: str, transcript_file: str, json_file: str) -> str:
    """Generate a ChatGPT prompt for claims analysis"""
    
    # Load episode data
    with open(json_file) as f:
        episodes = json.load(f)
        
    episode = next((ep for ep in episodes if ep["episode_id"] == episode_id), None)
    if not episode:
        raise Exception(f"Episode {episode_id} not found in database")
    
    # Get just the filename from the path
    transcript_filename = os.path.basename(transcript_file)
    
    # Create platform-specific prompt
    if episode.get("platform_type") == "youtube":
        prompt = f"""Please analyze this YouTube podcast episode:

Title: {episode['title']}
Channel: {episode['podcast_name']}
URL: {episode['share_url']}

Using the transcript from file: {transcript_filename}

Instructions:
1. Read the transcript carefully and analyze the full content
2. Respond with ONLY a single ```json codeblock
3. Keep all existing values - only fill in empty fields
4. Format timestamps as "HH:MM:SS"
5. For claims analysis, follow these guidelines:
   - Extract 8-20 claims based on content density
   - Include ONLY significant, unique, or noteworthy statements
   - Avoid redundant or minor points
   - Each claim should represent a distinct idea or insight
   - Use these filter categories:
     * "key point" - Core facts or main arguments
     * "unique perspective" - Novel viewpoints or interpretations
     * "groundbreaking idea" - Innovative or controversial concepts

   Quality over quantity: If the episode has fewer than 8 truly significant claims,
   that's fine. If it's packed with unique insights, include up to 20.
   Each claim should be substantial enough to warrant inclusion in a summary
   of the episode's key takeaways.

Required fields to complete:
- interviewee.name: Full name from transcript
- interviewee.profession: Main profession/title
- interviewee.organization: Current organization
- summary: 2-3 sentence episode overview
- claims: 8-20 significant, non-redundant statements with timestamps
- related_topics: 5-10 main subjects discussed
- tags: 5-10 searchable keywords

Format your response as JSON matching this structure:
{{
    "interviewee": {{
        "name": "Full Name",
        "profession": "Their Role",
        "organization": "Their Organization"
    }},
    "summary": "2-3 sentence episode overview...",
    "claims": [
        {{
            "claim_id": "1",
            "claim": "The specific claim or insight",
            "timestamp": "HH:MM:SS",
            "filter": "key point|unique perspective|groundbreaking idea",
            "segment": "early|middle|late"
        }}
    ],
    "related_topics": ["topic1", "topic2", "topic3", "topic4", "topic5"],
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}"""

    else:  # Vimeo
        prompt = f"""Please analyze this podcast episode:

Title: {episode['title']}
Show: {episode['podcast_name']}
URL: {episode['share_url']}

Using the transcript from file: {transcript_filename}

[Same detailed instructions as YouTube version...]"""

    return prompt