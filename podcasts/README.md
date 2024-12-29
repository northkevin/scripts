scripts/
├── podcasts/
│   ├── main.py             # Single CLI entry point
│   ├── fetch_vimeo.py      # Helper: fetch & parse data from a Vimeo embed URL
│   ├── transcript_utils.py # Helper: download & optionally transform .vtt
│   └── ...
├── (other scripts).py
└── ...

1. pip install requests

2. cd scripts/podcasts

3. parse-episode
python main.py parse-episode --vimeo_url "https://player.vimeo.com/video/1012842356"

4. get-transcript
python main.py get-transcript \
    --webvtt_link "/texttrack/186140220.vtt?token=XYZ" \
    --episode_id 002 \
    --slug jack_kruse

5. generate-prompt
python main.py generate-prompt \
    --episode_id 002 \
    --title "Jack Kruse Podcast" \
    --transcript_file "transcripts/002_jack_kruse.vtt"