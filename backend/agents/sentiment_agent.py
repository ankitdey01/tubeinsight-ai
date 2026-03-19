"""
backend/agents/sentiment_agent.py
───────────────────────────────────
Sentiment & Vibe Agent.
Uses LLM-powered analysis for deep qualitative sentiment insights.
Processes comments in chunks to handle large volumes.
"""
print(f"[LOADING] {__file__}")

from loguru import logger

from backend.core.llm_client import LLMClient
from backend.utils.preprocessing import chunk_comments_for_llm
from config.prompts import SENTIMENT_SYSTEM, SENTIMENT_USER


class SentimentAgent:
    def __init__(self):
        self.llm = LLMClient()

    def run(self, comments: list[dict], video_title: str) -> dict:
        """
        Run sentiment analysis on a list of comments using LLM-only approach.
        Processes comments in chunks and aggregates AI-generated sentiment data.
        """
        logger.info(f"SentimentAgent: Analyzing {len(comments)} comments")

        # 1. Sample up to 100 comments for LLM analysis (cost-conscious)
        # Prioritize high-like comments as they're more representative
        sorted_comments = sorted(comments, key=lambda x: x.get("like_count", 0), reverse=True)
        sample = sorted_comments[:100]

        # 2. Chunk and analyze with Claude
        chunks = chunk_comments_for_llm(sample, max_chars=6000, max_per_chunk=40)
        chunk_results = []

        for i, chunk_text in enumerate(chunks):
            logger.debug(f"Analyzing chunk {i+1}/{len(chunks)}")
            try:
                result = self.llm.complete_json(
                    user_prompt=SENTIMENT_USER.format(
                        video_title=video_title,
                        comments=chunk_text,
                    ),
                    system_prompt=SENTIMENT_SYSTEM,
                    max_tokens=800,  # Reduced for rate limits
                )
                chunk_results.append(result)
            except Exception as e:
                logger.warning(f"Chunk {i+1} failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue

        if not chunk_results:
            logger.error("All LLM chunks failed: sentiment analysis could not be completed")
            raise Exception(
                "Sentiment analysis failed for all comment chunks. "
                "Unable to produce AI-generated sentiment analysis. "
                "Please try again or check LLM service status."
            )

        # 3. Merge chunk results (use first chunk as base, aggregate lists)
        merged = chunk_results[0].copy()
        merged["comments_analyzed"] = len(sample)

        # Merge top items across chunks
        for key in ["top_praises", "top_criticisms", "top_questions"]:
            all_items = []
            for r in chunk_results:
                all_items.extend(r.get(key, []))
            merged[key] = list(dict.fromkeys(all_items))[:5]  # Dedupe, keep top 5

        # Aggregate sentiment_distribution across chunks (average percentages)
        if chunk_results:
            sentiment_dist = {"positive": 0, "negative": 0, "neutral": 0}
            for r in chunk_results:
                if "sentiment_distribution" in r:
                    for key in sentiment_dist.keys():
                        sentiment_dist[key] += r["sentiment_distribution"].get(key, 0)
            # Average the distributions
            num_chunks = len(chunk_results)
            for key in sentiment_dist.keys():
                sentiment_dist[key] = round(sentiment_dist[key] / num_chunks, 1)
            merged["sentiment_distribution"] = sentiment_dist

        logger.success("SentimentAgent complete")
        return merged
