import json

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

def generate_prompt(episode_id, transcript_file, json_file):
    """Generate ChatGPT prompt for completing episode metadata"""
    episode = find_episode_by_id(json_file, episode_id)
    
    prompt = f"""
You are an AI assistant helping to process podcast episode metadata. I need you to analyze a transcript and complete the episode information.

Current partial metadata:
{json.dumps(episode, indent=2)}

The transcript file is: '{transcript_file}'

IMPORTANT INSTRUCTIONS:
1. First, identify and note the total duration of the transcript (HH:MM:SS)
2. Analyze the ENTIRE transcript from beginning to end
3. Ensure your analysis covers the full timeline of the conversation
4. Claims should be distributed across different segments of the episode
5. Avoid clustering all claims from a single portion of the transcript

CLAIMS GUIDELINES:
- Extract 8-20 claims based on content density
- Include significant statements from throughout the episode
- Distribute claims across early, middle, and late segments
- Each claim should represent a distinct idea or insight
- Use these filter categories:
  * "key point" - Core facts or main arguments
  * "unique perspective" - Novel viewpoints or interpretations
  * "groundbreaking idea" - Innovative or controversial concepts

QUALITY CRITERIA:
- Quality over quantity: 8-20 claims depending on content density
- Each claim should be substantial and non-redundant
- Claims should represent the full scope of the conversation
- Timestamps should show coverage across the episode duration
- If the episode is lengthy (>1 hour), ensure later segments are analyzed

Required fields to complete:
- interviewee.name: Full name from transcript
- interviewee.profession: Main profession/title
- interviewee.organization: Current organization
- summary: 2-3 sentence episode overview
- claims: 8-20 significant statements with distributed timestamps
- related_topics: 5-10 main subjects discussed (from full episode)
- tags: 5-10 searchable keywords (reflecting complete content)
- duration: Total length of transcript (HH:MM:SS format)

Copy this template and fill in the empty fields:

```json
{{
  "episode_id": "{episode['episode_id']}",
  "title": "{episode['title']}",
  "share_url": "{episode['share_url']}",
  "podcast_name": "{episode['podcast_name']}",
  "interviewee": {{
    "name": "",
    "profession": "",
    "organization": ""
  }},
  "air_date": "{episode['air_date']}",
  "duration": "",
  "summary": "",
  "claims": [
    {{
      "claim_id": "1",
      "claim": "",
      "timestamp": "HH:MM:SS",
      "filter": "key point|unique perspective|groundbreaking idea",
      "segment": "early|middle|late"
    }}
  ],
  "related_topics": [],
  "tags": [],
  "webvtt_link": "{episode.get('webvtt_link', '')}",
  "transcript_file": "{episode.get('transcript_file', '')}"
}}
```

VALIDATION REQUIREMENTS:
1. Claims must include timestamps from all thirds of the episode
2. At least 20% of claims should come from the final third
3. No more than 40% of claims should come from any single third
4. Added "segment" field to help verify distribution
5. Include total duration to validate coverage

RESPONSE FORMAT:
1. Start with ```json
2. Paste and complete the template above
3. End with ```
4. No other text or explanations needed

Your response should be a single JSON code block that can be directly copied to update our database.
"""
    return prompt.strip()