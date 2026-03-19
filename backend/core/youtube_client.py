"""
backend/core/youtube_client.py
───────────────────────────────
YouTube Data API v3 wrapper.
Handles channel resolution, video listing, and comment fetching
with built-in rate-limit handling and retry logic.
"""
print(f"[LOADING] {__file__}")

import re
import json
from pathlib import Path
from typing import Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import get_settings


settings = get_settings()


class YouTubeClient:
    def __init__(self):
        self.service = build("youtube", "v3", developerKey=settings.youtube_api_key)
        self.raw_dir = Path(settings.raw_data_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    # ─── URL Parsing ──────────────────────────────────────────────────────────

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from any YouTube URL format."""
        patterns = [
            r"(?:v=|youtu\.be/|embed/|v/|shorts/)([a-zA-Z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def extract_channel_id(self, url: str) -> Optional[str]:
        """Resolve channel URL to a channel ID."""
        # Handle @handle format
        handle_match = re.search(r"@([\w.-]+)", url)
        if handle_match:
            handle = handle_match.group(1)
            return self._resolve_handle(handle)

        # Handle /channel/UC... format
        channel_match = re.search(r"/channel/(UC[\w-]+)", url)
        if channel_match:
            return channel_match.group(1)

        return None

    def _resolve_handle(self, handle: str) -> Optional[str]:
        """Resolve a @handle to a channel ID via the API."""
        try:
            response = self.service.channels().list(
                part="id", forHandle=handle
            ).execute()
            items = response.get("items", [])
            return items[0]["id"] if items else None
        except HttpError as e:
            logger.error(f"Failed to resolve handle @{handle}: {e}")
            return None

    # ─── Video Fetching ───────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_channel_videos(self, channel_id: str, max_results: int = None) -> list[dict]:
        """Fetch the latest N videos from a channel."""
        max_results = max_results or settings.max_videos_per_channel
        logger.info(f"Fetching latest {max_results} videos for channel {channel_id}")

        try:
            # Get uploads playlist ID
            channel_response = self.service.channels().list(
                part="contentDetails,snippet",
                id=channel_id
            ).execute()

            if not channel_response.get("items"):
                raise ValueError(f"Channel {channel_id} not found")

            channel_data = channel_response["items"][0]
            uploads_playlist = channel_data["contentDetails"]["relatedPlaylists"]["uploads"]
            channel_name = channel_data["snippet"]["title"]

            # Fetch videos from uploads playlist
            videos = []
            next_page_token = None

            while len(videos) < max_results:
                playlist_response = self.service.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=uploads_playlist,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                ).execute()

                for item in playlist_response.get("items", []):
                    videos.append({
                        "video_id": item["contentDetails"]["videoId"],
                        "title": item["snippet"]["title"],
                        "published_at": item["snippet"]["publishedAt"],
                        "thumbnail": item["snippet"]["thumbnails"].get("high", {}).get("url"),
                        "channel_id": channel_id,
                        "channel_name": channel_name,
                    })

                next_page_token = playlist_response.get("nextPageToken")
                if not next_page_token:
                    break

            logger.success(f"Found {len(videos)} videos for {channel_name}")
            return videos[:max_results]

        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_video_metadata(self, video_id: str) -> dict:
        """Fetch metadata for a single video."""
        response = self.service.videos().list(
            part="snippet,statistics,contentDetails",
            id=video_id
        ).execute()

        if not response.get("items"):
            raise ValueError(f"Video {video_id} not found")

        item = response["items"][0]
        snippet = item["snippet"]
        stats = item.get("statistics", {})

        return {
            "video_id": video_id,
            "title": snippet["title"],
            "description": snippet["description"][:1000],  # Truncate long descriptions
            "channel_id": snippet["channelId"],
            "channel_name": snippet["channelTitle"],
            "published_at": snippet["publishedAt"],
            "thumbnail": snippet["thumbnails"].get("high", {}).get("url"),
            "view_count": int(stats.get("viewCount", 0)),
            "like_count": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "url": f"https://youtube.com/watch?v={video_id}",
        }

    # ─── Comment Fetching ─────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_video_comments(self, video_id: str, max_comments: int = None) -> list[dict]:
        """
        Fetch top-level comments for a video.
        Returns cleaned comment objects ready for analysis.
        """
        max_comments = max_comments or settings.max_comments_per_video
        logger.info(f"Fetching up to {max_comments} comments for video {video_id}")

        comments = []
        next_page_token = None

        try:
            while len(comments) < max_comments:
                response = self.service.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=min(100, max_comments - len(comments)),
                    order="relevance",
                    pageToken=next_page_token,
                    textFormat="plainText"
                ).execute()

                for item in response.get("items", []):
                    top = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append({
                        "comment_id": item["id"],
                        "video_id": video_id,
                        "text": top["textDisplay"],
                        "author": top["authorDisplayName"],
                        "like_count": top.get("likeCount", 0),
                        "published_at": top["publishedAt"],
                        "reply_count": item["snippet"].get("totalReplyCount", 0),
                    })

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

            logger.success(f"Fetched {len(comments)} comments for {video_id}")

            # Cache raw data
            cache_path = self.raw_dir / f"{video_id}_comments.json"
            cache_path.write_text(json.dumps(comments, indent=2))

            return comments

        except HttpError as e:
            if e.resp.status == 403:
                logger.warning(f"Comments disabled for video {video_id}")
                return []
            raise
