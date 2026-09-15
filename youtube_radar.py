"""Public YouTube data used by the Radar de Canais em Ascensão."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import requests


API_URL = "https://www.googleapis.com/youtube/v3"


def _get(resource: str, params: dict) -> dict:
    response = requests.get(f"{API_URL}/{resource}", params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def _number(value: str | None) -> int:
    try:
        return int(value or 0)
    except ValueError:
        return 0


def find_rising_videos(api_key: str, niche: str, days: int = 14, limit: int = 12) -> list[dict]:
    """Find recent public videos and rank them by transparent momentum signals."""
    if not api_key:
        raise ValueError("Configure YOUTUBE_DATA_API_KEY em Streamlit Secrets.")
    if not niche.strip():
        raise ValueError("Informe um nicho para pesquisar.")

    published_after = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")
    search = _get("search", {
        "key": api_key, "part": "snippet", "q": niche.strip(), "type": "video",
        "order": "date", "publishedAfter": published_after, "maxResults": min(limit * 3, 50),
        "videoDuration": "short",
    })
    video_ids = [item.get("id", {}).get("videoId") for item in search.get("items", [])]
    video_ids = [video_id for video_id in video_ids if video_id]
    if not video_ids:
        return []

    videos = _get("videos", {"key": api_key, "part": "snippet,statistics", "id": ",".join(video_ids)})
    channel_ids = list({item["snippet"]["channelId"] for item in videos.get("items", [])})
    channels = _get("channels", {"key": api_key, "part": "snippet,statistics", "id": ",".join(channel_ids)})
    channel_info = {item["id"]: item for item in channels.get("items", [])}

    ranked = []
    now = datetime.now(timezone.utc)
    for video in videos.get("items", []):
        snippet = video["snippet"]
        published = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
        age_days = max((now - published).total_seconds() / 86400, 0.25)
        views = _number(video.get("statistics", {}).get("viewCount"))
        views_per_day = views / age_days
        channel = channel_info.get(snippet["channelId"], {})
        subscribers = _number(channel.get("statistics", {}).get("subscriberCount"))
        relative_reach = views / max(subscribers, 1)
        # The score is deliberately an indicator, not a claim of future virality.
        score = min(100, round(10 * math.log10(views_per_day + 1) + 18 * min(relative_reach, 2)))
        ranked.append({
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "video_url": f"https://www.youtube.com/watch?v={video['id']}",
            "channel_url": f"https://www.youtube.com/channel/{snippet['channelId']}",
            "views": views,
            "views_per_day": round(views_per_day),
            "age_days": max(1, round(age_days)),
            "subscribers": subscribers,
            "score": score,
            "signal": "Muito forte" if score >= 60 else "Bom sinal" if score >= 35 else "Em observação",
        })
    return sorted(ranked, key=lambda item: (item["score"], item["views_per_day"]), reverse=True)[:limit]
