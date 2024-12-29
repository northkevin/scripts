#!/usr/bin/env python3
# scripts/podcasts/main.py

import argparse
import os
import json

from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

from fetch_vimeo import get_vimeo_data_headless
from transcript_utils import download_vtt_file
from generate_prompt import generate_prompt


# ------------------------------------------------------------
# Logging Setup
# ------------------------------------------------------------
LOG_FILE = "script.log"

handler = RotatingFileHandler(LOG_FILE, maxBytes=200_000, backupCount=2)  # ~200 KB before rotating
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)

logger = logging.getLogger("podcast_cli")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

def log_print(msg: str):
    """
    Print to console and also log to rotating file.
    """
    print(msg)
    logger.info(msg)

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
BASE_DIR = Path(__file__).parent
DEFAULT_JSON_FILE = BASE_DIR / "Podcast Data" / "test.json"
TRANSCRIPTS_DIR = BASE_DIR / "Podcast Data" / "transcripts"
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)


# ------------------------------------------------------------
# 1) parse-episode: get data from Vimeo URL
# ------------------------------------------------------------
def cmd_parse_episode(args):
    """
    Usage: python main.py parse-episode --vimeo_url "https://player.vimeo.com/video/1012842356"
    """
    try:
        data = get_vimeo_data_headless(args.vimeo_url)
    except Exception as e:
        log_print(f"Error fetching with Selenium: {e}")
        return

    player_data = data["playerConfig"]     # window.playerConfig dict
    ld_json_list = data["ld_json"]         # all ld+json blocks
    page_source = data["page_source"]      # raw HTML (if needed)

    # 1) Possibly find the "VideoObject" from ld_json
    ld_video = next((x for x in ld_json_list if x.get("@type") == "VideoObject"), {})

    # 2) Determine the webvtt link if available
    text_tracks = player_data.get("request", {}).get("text_tracks", [])
    webvtt_link = ""
    if text_tracks:
        # We'll just pick the first track's "url" if it exists
        raw_url = text_tracks[0].get("url", "")
        # Combine with "https://player.vimeo.com" if it's a relative path
        if raw_url.startswith("/"):
            webvtt_link = "https://player.vimeo.com" + raw_url
        else:
            webvtt_link = raw_url

    # 3) Build final snippet
    video_id = str(player_data.get("video", {}).get("id", "unknown"))
    final_dict = {
        "episode_id": video_id,
        "title": ld_video.get("name", player_data.get("video", {}).get("title", "")),
        "share_url": player_data.get("video", {}).get("share_url", ""),
        "podcast_name": player_data.get("video", {}).get("owner", {}).get("name", "<MANUAL>"),
        "interviewee": {
            "name": "<MANUAL>",
            "profession": "",
            "organization": "<MANUAL>"
        },
        "air_date": ld_video.get("uploadDate", ""),
        "summary": ld_video.get("description", ""),
        "claims": [],
        "related_topics": [],
        "tags": [],
        # The new "webvtt_link" property:
        "webvtt_link": webvtt_link,
        # A possible default transcript filename
        "transcript_file": f"transcripts/{video_id}_podcast_jack_kruse.txt"
    }

    snippet_json = json.dumps(final_dict, indent=2)
    log_print("Here is the combined JSON snippet:")
    log_print(snippet_json)

# ------------------------------------------------------------
# 2) get-transcript: download the .vtt
# ------------------------------------------------------------
def cmd_get_transcript(args):
    """
    Usage Example:
      python main.py get-transcript \
        --texttrack_id "186140220" \
        --token "TOKEN" \
        --episode_id "1012842356" \
        --slug "jack_kruse"

    This combines them into:
      https://player.vimeo.com/texttrack/<texttrack_id>.vtt?token=<token>

    And downloads .vtt -> transcripts/1012842356_jack_kruse.vtt
    """
    base_dir = Path(__file__).parent
    transcripts_dir = base_dir / "Podcast Data" / "transcripts"
    os.makedirs(transcripts_dir, exist_ok=True)

    out_filename = f"{args.episode_id}_{args.slug}.vtt"
    out_path = transcripts_dir / out_filename

    # 1) Build final .vtt URL
    texttrack_id = args.texttrack_id
    token = args.token
    webvtt_link = f"https://player.vimeo.com/texttrack/{texttrack_id}.vtt?token={token}"

    try:
        log_print(f"Downloading .vtt from {webvtt_link}")
        download_vtt_file(webvtt_link, out_path.as_posix())
        log_print(f"Transcript file saved => {out_path}")
    except Exception as e:
        log_print(f"Error downloading transcript: {e}")


# ------------------------------------------------------------
# generate-prompt: produce ChatGPT prompt for top 10 claims
# ------------------------------------------------------------
def cmd_generate_prompt(args):
    """
    Generate ChatGPT prompt for a specific episode using data from the JSON file.

    Usage:
      python main.py generate-prompt \
        --episode_id "1012842356" \
        --transcript_file "Podcast Data/transcripts/1012842356_podcast_jack_kruse.txt" \
        --json_file "/path/to/json/file.json"
    """
    json_file_path = args.json_file or DEFAULT_JSON_FILE
    prompt = generate_prompt(args.episode_id, args.transcript_file, json_file_path)
    print("\n--- ChatGPT Prompt ---\n")
    print(prompt)
    print("\n-----------------------")

# ------------------------------------------------------------
# Main CLI
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Podcast CLI with minimal sub-commands.")
    sub = parser.add_subparsers(dest="command")

    # parse-episode
    p_parse = sub.add_parser("parse-episode", help="Parse basic data from a Vimeo embed URL.")
    p_parse.add_argument("--vimeo_url", required=True)

    # get-transcript command
    p_trans = sub.add_parser("get-transcript", help="Download .vtt transcript to local file using texttrack_id & token.")
    p_trans.add_argument("--texttrack_id", required=True, help="The numeric ID e.g. '186140220'.")
    p_trans.add_argument("--token", required=True, help="The token e.g. '0xfc48b2c22e66093a...'")
    p_trans.add_argument("--episode_id", required=True, help="Unique episode identifier, e.g. '1012842356'.")
    p_trans.add_argument("--slug", required=True, help="Short descriptor for the transcript filename, e.g. 'jack_kruse'.")
    p_trans.set_defaults(func=cmd_get_transcript)

    # ----------------------
    # generate-prompt command
    # ----------------------
    p_prompt = sub.add_parser("generate-prompt", help="Generate a ChatGPT prompt for top 10 claims, referencing transcript.")
    p_prompt.add_argument("--episode_id", required=True, help="E.g. '1012842356'")
    p_prompt.add_argument("--transcript_file", required=True, help="Path to the local .vtt or .txt transcript file.")
    p_prompt.add_argument("--json_file", help="Path to the JSON database file. Defaults to the internal path.")
    p_prompt.set_defaults(func=cmd_generate_prompt)

    args = parser.parse_args()

    if args.command == "parse-episode":
        cmd_parse_episode(args)
    elif args.command == "get-transcript":
        cmd_get_transcript(args)
    elif args.command == "generate-prompt":
        cmd_generate_prompt(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()