from typing import TypedDict, List, Literal

class Interviewee(TypedDict):
    name: str
    profession: str
    organization: str

class Claim(TypedDict):
    claim_id: str
    claim: str
    timestamp: str
    filter: Literal["key point", "unique perspective", "groundbreaking idea"]
    segment: Literal["early", "middle", "late"]

class PodcastEpisode(TypedDict):
    episode_id: str
    platform_type: Literal["youtube", "vimeo"]
    title: str
    share_url: str
    podcast_name: str
    interviewee: Interviewee
    air_date: str
    duration: str
    summary: str
    claims: List[Claim]
    related_topics: List[str]
    tags: List[str]
    webvtt_link: str
    transcript_file: str

# Default template for new episodes
EPISODE_TEMPLATE = {
    "episode_id": "",
    "platform_type": "",
    "title": "",
    "share_url": "",
    "podcast_name": "",
    "interviewee": {
        "name": "<MANUAL>",
        "profession": "<MANUAL>",
        "organization": "<MANUAL>"
    },
    "air_date": "",
    "duration": "",
    "summary": "<MANUAL>",
    "claims": [],
    "related_topics": [],
    "tags": [],
    "webvtt_link": "",
    "transcript_file": ""
} 