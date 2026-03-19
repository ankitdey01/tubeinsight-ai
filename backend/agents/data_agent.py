"""
backend/agents/data_agent.py
──────────────────────────────
Data Ingestion Agent.
Fetches video metadata + comments, preprocesses them,
and stores embeddings in the vector store.
"""
print(f"[LOADING] {__file__}")

from loguru import logger

from backend.core.youtube_client import YouTubeClient
from backend.core.embeddings import EmbeddingClient
from backend.core.vectorstore import VectorStore
from backend.utils.preprocessing import preprocess_comments


class DataAgent:
    def __init__(self):
        self.yt = YouTubeClient()
        self.embedder = EmbeddingClient()
        self.vs = VectorStore()

    def run(
        self,
        video_id: str,
        force_refresh: bool = False,
        max_comments: int | None = None,
    ) -> dict:
        """
        Full ingestion pipeline for a video.
        - Fetches metadata + comments from YouTube API
        - Cleans and filters comments
        - Embeds and stores in ChromaDB
        Returns dict with metadata + comment lists.
        """
        logger.info(f"DataAgent: Processing video {video_id}")

        # Skip re-embedding if already indexed (unless forced)
        already_indexed = self.vs.collection_exists(video_id)

        # Fetch metadata
        metadata = self.yt.get_video_metadata(video_id)
        logger.info(f"Video: '{metadata['title']}' | {metadata['comment_count']} total comments")
        logger.debug(f"Metadata: {metadata}")

        # Fetch comments
        raw_comments = self.yt.get_video_comments(video_id, max_comments=max_comments)
        logger.debug(f"Raw comments: {raw_comments}")

        # Preprocess
        clean_comments = preprocess_comments(raw_comments)
        logger.debug(f"Clean comments: {clean_comments}")

        if not clean_comments:
            raise ValueError(f"No valid comments found for video {video_id}")

        # Embed and store (skip if already indexed)
        if not already_indexed or force_refresh:
            logger.info(f"Embedding {len(clean_comments)} comments and storing in vector store for video {video_id}...")
            texts = [c["text"] for c in clean_comments]
            logger.debug(f"Texts to embed: {texts}")
            embeddings = self.embedder.embed_texts(texts)
            logger.debug(f"Embeddings: {embeddings}")
            logger.info(f"Got {len(embeddings)} embeddings, storing in vector store...")
            self.vs.upsert_comments(video_id, clean_comments, embeddings)
            logger.info(f"Successfully stored comments for video {video_id}")
        else:
            logger.info(f"Video {video_id} already indexed, skipping re-embedding")

        return {
            "metadata": metadata,
            "raw_comments": raw_comments,
            "clean_comments": clean_comments,
        }
