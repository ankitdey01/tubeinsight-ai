"""
backend/agents/report_agent.py
────────────────────────────────
Report Generation Agent.
Synthesizes all analysis results into a polished written report.
"""
print(f"[LOADING] {__file__}")

import json
from loguru import logger

from backend.core.llm_client import LLMClient
from config.prompts import REPORT_SYSTEM, REPORT_USER


class ReportAgent:
    def __init__(self):
        self.llm = LLMClient()

    def run(
        self,
        video_metadata: dict,
        sentiment: dict,
        topics: dict,
        total_comments: int,
    ) -> str:
        """
        Generate a polished insight report.
        Returns markdown-formatted report string.
        """
        logger.info(f"ReportAgent: Generating report for '{video_metadata['title']}'")

        try:
            report = self.llm.complete(
                user_prompt=REPORT_USER.format(
                    video_title=video_metadata["title"],
                    video_url=video_metadata.get("url", ""),
                    total_comments=total_comments,
                    sentiment_data=json.dumps(sentiment, indent=2),
                    topic_data=json.dumps(topics, indent=2),
                ),
                system_prompt=REPORT_SYSTEM,
                max_tokens=1200,  # Reduced for rate limits
                temperature=0.4,  # Slightly more creative for narrative writing
            )
            logger.success("ReportAgent: Report generated")
            return report
        except Exception as e:
            logger.warning(f"LLM report generation failed: {e}, using fallback")
            # Fallback: generate basic report from data
            overall = sentiment.get("overall_sentiment", "unknown")
            vibe = sentiment.get("vibe_score", "N/A")
            topic_list = topics.get("topics", [])
            topic_names = [t.get("label", f"Theme {i+1}") for i, t in enumerate(topic_list[:5])]
            
            return f"""# Video Analysis Report: {video_metadata['title']}

## Executive Summary
This video received **{overall}** sentiment with a vibe score of **{vibe}/10**. 
Analyzed {total_comments} comments.

## Sentiment Overview
- Overall: {overall.capitalize()}
- Vibe Score: {vibe}/10
- Likeness Score: {sentiment.get('likeness_score', 'N/A')}/10
- Comments Analyzed: {sentiment.get('comments_analyzed', total_comments)}

## Key Themes Identified
{chr(10).join(f"- {name}" for name in topic_names) if topic_names else "- No specific themes identified"}

## Notes
*This is a basic automated report. Full AI-generated insights are temporarily unavailable.*
"""
