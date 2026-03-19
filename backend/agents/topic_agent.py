"""
backend/agents/topic_agent.py
───────────────────────────────
Topic Clustering Agent.
Uses KMeans on comment embeddings to discover themes,
then uses Claude to label each cluster meaningfully.
"""
print(f"[LOADING] {__file__}")

import json
import numpy as np
from loguru import logger
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize

from backend.core.vectorstore import VectorStore
from backend.core.embeddings import EmbeddingClient
from backend.core.llm_client import LLMClient
from config.prompts import TOPIC_SYSTEM, TOPIC_USER


class TopicAgent:
    def __init__(self):
        self.vs = VectorStore()
        self.embedder = EmbeddingClient()
        self.llm = LLMClient()

    def _cluster_comments(
        self,
        comments: list[dict],
        n_clusters: int = 6,
    ) -> list[dict]:
        """
        KMeans clustering on comment embeddings.
        Returns list of cluster dicts with representative comments.
        """
        texts = [c["text"] for c in comments]

        # Get embeddings
        embeddings = self.embedder.embed_texts(texts)
        X = np.array(embeddings)
        X = normalize(X)  # Normalize for cosine similarity

        # Fit KMeans
        n_clusters = min(n_clusters, len(comments))
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        labels = km.fit_predict(X)

        # Group comments by cluster
        clusters = {}
        for i, (comment, label) in enumerate(zip(comments, labels)):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(comment)

        # Build cluster objects with representative samples
        cluster_list = []
        for cluster_id, cluster_comments in clusters.items():
            # Sort by like count to pick best representatives
            sorted_c = sorted(cluster_comments, key=lambda x: x.get("like_count", 0), reverse=True)
            representatives = [c["text"] for c in sorted_c[:3]]

            cluster_list.append({
                "id": int(cluster_id),
                "size": len(cluster_comments),
                "representative_comments": representatives,
            })

        # Sort by size descending
        cluster_list.sort(key=lambda x: x["size"], reverse=True)
        return cluster_list

    def run(
        self,
        video_id: str,
        comments: list[dict],
        video_title: str,
        n_clusters: int = 6,
    ) -> dict:
        """Cluster comments and label them with Claude."""
        logger.info(f"TopicAgent: Clustering {len(comments)} comments into {n_clusters} topics")

        if len(comments) < n_clusters:
            n_clusters = max(2, len(comments) // 2)

        # Cluster
        raw_clusters = self._cluster_comments(comments, n_clusters=n_clusters)
        logger.debug(f"Formed {len(raw_clusters)} clusters")

        # Label with Claude
        try:
            clusters_text = json.dumps(raw_clusters, indent=2)
            result = self.llm.complete_json(
                user_prompt=TOPIC_USER.format(
                    video_title=video_title,
                    clusters=clusters_text,
                ),
                system_prompt=TOPIC_SYSTEM,
                max_tokens=1200,  # Reduced for rate limits
            )
            logger.success(f"TopicAgent: Identified {len(result.get('topics', []))} topics")
            return result
        except Exception as e:
            logger.warning(f"LLM topic labeling failed: {e}, using fallback")
            # Fallback: return clusters without LLM labels
            fallback_topics = []
            for i, cluster in enumerate(raw_clusters[:6]):
                fallback_topics.append({
                    "id": cluster["id"],
                    "label": f"Theme {i+1}",
                    "description": f"Cluster of {cluster['size']} similar comments",
                    "sentiment": "neutral",
                    "size": cluster["size"],
                    "representative_comments": cluster["representative_comments"][:3],
                })
            return {"topics": fallback_topics}
