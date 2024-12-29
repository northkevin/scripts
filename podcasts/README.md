# Podcast Processing Tools

Process podcast episodes from Vimeo URLs to structured JSON data with transcripts and claims analysis.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

The tool maintains state between commands so you don't need to manually track IDs and files.

### 1. Extract Episode Info
Start with the Vimeo URL:
```bash
python main.py parse-episode --vimeo_url "https://player.vimeo.com/video/1012842356"
```

This will:
- Extract episode metadata
- Find transcript information
- Save state for next step
- Show you the next command to run

### 2. Download Transcript
Run the suggested command (or just):
```bash
python main.py get-transcript
```

This will:
- Use saved state from previous step
- Download the transcript file
- Save state for next step
- Show you the next command to run

### 3. Generate Claims Prompt
Run the suggested command (or just):
```bash
python main.py generate-prompt
```

This will:
- Use saved state from previous steps
- Generate a ChatGPT prompt for claims analysis
- Include relevant transcript sections

## Project Structure
```
podcasts/
├── main.py             # Main CLI tool
├── fetch_vimeo.py      # Vimeo data extraction
├── transcript_utils.py # Transcript processing
├── generate_prompt.py  # Prompt generation
└── Podcast Data/      # Output directory
    ├── transcripts/   # Downloaded transcripts
    └── .current_episode.json  # State tracking
```

## State Management

The tool maintains state in `.current_episode.json` to track:
- Current episode ID
- Transcript file location
- Episode metadata

This eliminates the need to copy/paste information between steps.

## Manual Override

While the tool maintains state automatically, you can still provide arguments manually:

```bash
# Specify episode ID manually
python main.py get-transcript --episode_id "1012842356"

# Specify transcript file manually
python main.py generate-prompt --episode_id "1012842356" --transcript_file "path/to/transcript.vtt"
```

## Notes
- Each command suggests the next command to run
- Transcripts are saved in .vtt format
- State is maintained in the Podcast Data directory