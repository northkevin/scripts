# Podcast Processing Tools

Process podcast episodes from YouTube and Vimeo URLs to structured JSON data with transcripts and claims analysis.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. For YouTube functionality:
   - Get a YouTube API key from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Enable the YouTube Data API v3
   - Set your API key:
   ```bash
   export YOUTUBE_API_KEY="your-key-here"
   ```

## Testing the CLI

### Test Case 1: YouTube Episode
```bash
# 1. Process a YouTube podcast episode (gets metadata & transcript)
python main.py parse-youtube --url "https://www.youtube.com/watch?v=AaDq8g7II_E"

# Expected output:
# Video Info:
# ID: AaDq8g7II_E
# Title: Annie Jacobsen: The Pentagon's NUCLEAR WAR Files Uncovered
# Channel: Danny Jones
# Transcript saved to: Podcast Data/youtube/AaDq8g7II_E_transcript.vtt

# 2. Generate claims prompt for ChatGPT
python main.py generate-prompt

# Expected output:
# - ChatGPT prompt containing:
#   * Episode metadata
#   * Path to transcript
#   * Instructions for analysis
```

### Verifying Results

After running commands, check:

1. Metadata files:
```bash
# Check current state
cat "Podcast Data/.current_episode.json"

# Check database
cat "Podcast Data/podcast_data.json"

# Check transcript
cat "Podcast Data/youtube/AaDq8g7II_E_transcript.vtt"
```

2. Generated files should include:
- Episode metadata in JSON format
- Transcript in .vtt format
- ChatGPT prompt ready for analysis

### Example Workflow

1. Process YouTube video:
```bash
# Get metadata and transcript
python main.py parse-youtube --url "https://www.youtube.com/watch?v=AaDq8g7II_E"
```

2. Generate ChatGPT prompt:
```bash
# Uses saved state from previous step
python main.py generate-prompt

# Or specify files manually
python main.py generate-prompt \
  --episode_id "AaDq8g7II_E" \
  --transcript_file "Podcast Data/youtube/AaDq8g7II_E_transcript.vtt"
```

3. Copy the generated prompt to ChatGPT to get:
- Interviewee details
- Episode summary
- Key claims with timestamps
- Related topics
- Tags

4. Save ChatGPT's response to update the episode data in:
`Podcast Data/podcast_data.json`

## Notes
- Each command maintains state for the next step
- Transcripts are saved in .vtt format
- Platform-specific data is organized in separate directories
- YouTube functionality requires an API key
- Claims analysis requires ChatGPT prompt completion