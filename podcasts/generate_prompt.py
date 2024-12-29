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

def generate_prompt(episode_id, transcript_file, json_file_path):
    """
    Generate a prompt for ChatGPT based on an episode ID and transcript.

    Args:
        episode_id (str): The ID of the podcast episode.
        transcript_file (str): Path to the transcript file.
        json_file_path (str): Path to the JSON file containing episode metadata.

    Returns:
        str: The prompt for ChatGPT or an error message.
    """
    current_json = find_episode_by_id(json_file_path, episode_id)
    if not current_json:
        return f"Error: Episode with ID {episode_id} not found in {json_file_path}."

    # Assemble the prompt
    prompt = f"""
You are ChatGPT. I have a podcast transcript from the episode:

{json.dumps(current_json, indent=4)}

The transcript file is named '{transcript_file}'.

I want you to read the entire transcript and produce a list of the top 10 claims made in this episode, focusing on unique or noteworthy points.

Output your response as **valid JSON** under a key called "claims". For example:
{{
  "claims": [
    {{
      "claim_id": "1",
      "claim": "...",
      "timestamp": "00:00:00"
    }},
    ...
  ]
}}

If timestamps are unclear, you may approximate or omit them. Keep your claims concise but clear.
"""
    return prompt.strip()