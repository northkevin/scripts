# scripts/podcasts/fetch_vimeo.py

import logging
import re
import json
import time

logger = logging.getLogger("podcast_cli")

def _extract_player_config(page_source: str) -> str:
    """
    Balanced brace approach to extract the JSON for window.playerConfig = { ... }.
    """
    logger.debug("Using balanced brace approach for window.playerConfig.")

    start_match = re.search(r'window\.playerConfig\s*=\s*\{', page_source)
    if not start_match:
        logger.debug("No match for 'window.playerConfig = {' in page source.")
        raise ValueError("No window.playerConfig found.")

    start_index = start_match.end() - 1  # position of the '{'
    brace_count = 0
    end_index = None

    for i, ch in enumerate(page_source[start_index:], start=start_index):
        if ch == '{':
            brace_count += 1
        elif ch == '}':
            brace_count -= 1
            if brace_count == 0:
                end_index = i
                break

    if end_index is None:
        logger.debug("Couldn't find matching '}' for playerConfig.")
        raise ValueError("Could not find matching '}' for playerConfig JSON.")

    raw_json = page_source[start_index:end_index+1]
    logger.debug("Captured window.playerConfig (partial debug): %s", raw_json[:500])
    return raw_json

def _parse_ld_json(page_source: str) -> list:
    """
    Finds all <script type="application/ld+json">...</script> blocks
    in page_source, returns them as a list of dicts.
    """
    logger.debug("Searching for <script type='application/ld+json'> blocks.")
    pattern = r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>'
    matches = re.findall(pattern, page_source, re.DOTALL)

    results = []
    for idx, raw_str in enumerate(matches):
        raw_str = raw_str.strip()
        try:
            data = json.loads(raw_str)
            results.append(data)
            logger.debug("Parsed one ld+json block (index=%d).", idx)
        except json.JSONDecodeError as e:
            logger.debug("Error parsing ld+json block (index=%d): %s", idx, e)
    return results

def get_vimeo_data_headless(vimeo_url: str):
    """
    Launch a headless Chrome (Selenium), load the Vimeo embed page,
    and parse:
      1) window.playerConfig (balanced braces)
      2) <script type='application/ld+json'> blocks

    Returns:
      {
        "playerConfig": {...},     # dict from window.playerConfig
        "ld_json": [ {...}, ...],  # list of dicts from ld+json
        "page_source": "..."       # raw HTML if you need further parsing
      }
    """
    logger.debug(f"Initializing headless browser to load: {vimeo_url}")

    # Importing selenium here so the script won't fail if it's not installed elsewhere
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(vimeo_url)
        time.sleep(3)  # wait for JavaScript

        page_source = driver.page_source
        logger.debug("Headless browser page_source length=%d", len(page_source))

        # 1) Extract playerConfig
        raw_json = _extract_player_config(page_source)
        player_data = json.loads(raw_json)
        logger.debug("Successfully parsed window.playerConfig.")

        # 2) Extract ld+json blocks
        ld_json_list = _parse_ld_json(page_source)
        logger.debug("Found %d ld+json blocks.", len(ld_json_list))

        return {
            "playerConfig": player_data,
            "ld_json": ld_json_list,
            "page_source": page_source
        }
    finally:
        logger.debug("Quitting headless browser.")
        driver.quit()