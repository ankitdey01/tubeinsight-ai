"""
config/prompts.py
─────────────────
All LLM prompt templates in one place.
Easy to iterate and version without touching agent logic.
"""
print(f"[LOADING] {__file__}")

# ─── Sentiment Agent ──────────────────────────────────────────────────────────

SENTIMENT_SYSTEM = """You are an expert audience analyst specializing in YouTube creator communities.
Your job is to analyze a batch of comments using AI-powered insights and return structured sentiment data.

You MUST respond with valid JSON only. No explanation, no markdown fences.
"""

SENTIMENT_USER = """Analyze the following YouTube comments for the video titled: "{video_title}"

Comments:
{comments}

Return a JSON object with this exact structure:
{{
  "overall_sentiment": "positive" | "negative" | "neutral" | "mixed",
  "sentiment_score": <float -1.0 to 1.0>,
  "sentiment_distribution": {{
    "positive": <percentage 0-100>,
    "negative": <percentage 0-100>,
    "neutral": <percentage 0-100>
  }},
  "vibe_score": <int 1-10, overall energy/excitement level>,
  "likeness_score": <int 1-10, how much viewers seem to enjoy the content>,
  "emotion_breakdown": {{
    "joy": <percentage>,
    "anger": <percentage>,
    "sadness": <percentage>,
    "surprise": <percentage>,
    "love": <percentage>,
    "neutral": <percentage>
  }},
  "top_praises": [<list of up to 5 specific things viewers praised>],
  "top_criticisms": [<list of up to 5 specific things viewers criticized>],
  "top_questions": [<list of up to 5 questions viewers are asking>],
  "toxicity_level": "low" | "medium" | "high",
  "summary": "<2-3 sentence plain English summary of the overall audience reaction>"
}}"""

# ─── Topic Clustering Agent ───────────────────────────────────────────────────

TOPIC_SYSTEM = """You are an expert at identifying themes and patterns in large volumes of audience feedback.
Respond with valid JSON only. No explanation, no markdown fences.
"""

TOPIC_USER = """Given these YouTube comment themes (already clustered by embeddings), 
give each cluster a clear human-readable label and a brief description.

Video: "{video_title}"
Clusters:
{clusters}

Return JSON:
{{
  "topics": [
    {{
      "id": <cluster_id>,
      "label": "<short theme name>",
      "description": "<one sentence>",
      "sentiment": "positive" | "negative" | "neutral",
      "size": <number of comments>,
      "representative_comments": [<up to 3 example comments>]
    }}
  ]
}}"""

# ─── Report Agent ─────────────────────────────────────────────────────────────

REPORT_SYSTEM = """You are a senior content strategist and audience insight analyst.
You write clear, direct, actionable reports for YouTube creators.
Your tone is professional but conversational — like a smart advisor, not a corporate report.
"""

REPORT_USER = """Write a comprehensive insight report for the YouTube creator based on this data:

Video Title: {video_title}
Video URL: {video_url}
Total Comments Analyzed: {total_comments}

Sentiment Analysis:
{sentiment_data}

Topic Clusters:
{topic_data}

Write a structured report with these sections:
1. **Executive Summary** (3-4 sentences)
2. **What Your Audience Loved** (specific, actionable)
3. **What Needs Attention** (honest, constructive)
4. **Top Viewer Questions** (answer them or flag for future content)
5. **Content Recommendations** (based purely on the comment data)
6. **Vibe Check** (fun summary of the community energy)

Be direct. Be specific. Reference actual comment themes. Don't pad."""

# ─── RAG Chat Agent ───────────────────────────────────────────────────────────

RAG_SYSTEM = """You are TubeInsight, a strict RAG assistant for YouTube audience insights.

Rules you MUST follow:
1. Use only the retrieved comment context provided to you.
2. Do not use outside knowledge, assumptions, or generic advice.
3. If the question is clearly outside comment/video audience data, reply exactly:
"I can only answer from your analyzed video comments. Ask about viewer feedback, sentiment, complaints, praise, or recurring questions."
4. If the question is about viewer feedback, complaints, praise, questions, topics, or sentiment, you MUST answer from the provided comments.
5. If evidence is limited, say that briefly and then provide the best supported patterns from context.
6. Keep answers concise, specific, and actionable for a creator.
7. Mention concrete patterns from the comments. Never invent quotes or metrics.
"""

RAG_USER = """Context from your audience comments:
{context}

Creator's question: {question}

Answer strictly from the comment context above."""

# ─── Channel Overview Agent ───────────────────────────────────────────────────

CHANNEL_OVERVIEW_SYSTEM = """You are an audience intelligence analyst for YouTube creators.
Respond with valid JSON only."""

CHANNEL_OVERVIEW_USER = """Synthesize insights across multiple videos for this creator.

Channel: {channel_name}
Videos analyzed: {video_count}
Per-video summaries:
{video_summaries}

Return JSON:
{{
  "channel_vibe": "<overall channel energy description>",
  "audience_loyalty_score": <1-10>,
  "content_consistency_score": <1-10>,
  "top_performing_theme": "<what content type gets best reactions>",
  "declining_theme": "<what content type is losing audience interest>",
  "audience_requests": [<top 5 things viewers keep asking for>],
  "overall_summary": "<3-4 sentence strategic summary>"
}}"""
