import time
from typing import Any

import requests


YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIError(RuntimeError):
    pass


def _request(path: str, params: dict[str, Any], retries: int = 3) -> dict[str, Any]:
    url = f"{YOUTUBE_API_BASE}/{path}"
    for attempt in range(retries + 1):
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        if response.status_code in {429, 500, 502, 503, 504} and attempt < retries:
            time.sleep(2 ** attempt)
            continue
        raise YouTubeAPIError(f"YouTube API error {response.status_code}: {response.text}")
    raise YouTubeAPIError("YouTube API failed after retries")


def search_list(
    api_key: str,
    query: str,
    published_after: str,
    region_code: str | None,
    relevance_language: str | None,
    max_results: int = 25,
) -> dict[str, Any]:
    params = {
        "key": api_key,
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": "date",
        "publishedAfter": published_after,
        "maxResults": max_results,
    }
    if region_code:
        params["regionCode"] = region_code
    if relevance_language:
        params["relevanceLanguage"] = relevance_language
    return _request("search", params)


def videos_list(api_key: str, video_ids: list[str]) -> dict[str, Any]:
    params = {
        "key": api_key,
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(video_ids),
        "maxResults": len(video_ids),
    }
    return _request("videos", params)


def channels_list(api_key: str, channel_ids: list[str]) -> dict[str, Any]:
    params = {
        "key": api_key,
        "part": "snippet,statistics",
        "id": ",".join(channel_ids),
        "maxResults": len(channel_ids),
    }
    return _request("channels", params)
