"""
api.py
────────────────
TubeInsight AI — FastAPI Backend

Exposes the LangGraph agent pipeline and RAG chat as REST endpoints.
"""

import sys
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

# Ensure project root is in path
sys.path.insert(0, ".")

from backend.core.youtube_client import YouTubeClient
from backend.agents.orchestrator import TubeInsightPipeline
from backend.agents.rag_agent import RAGAgent


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    youtube_url: str


class AnalyzeResponse(BaseModel):
    sentiment: dict
    top_comments: list[str]
    channel_insights: dict
    agent_summaries: dict
    video_metadata: dict


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    response: str


class HealthResponse(BaseModel):
    status: str


# ─── Global State ─────────────────────────────────────────────────────────────

# Store the current video_id for RAG context across requests
_current_video_id: Optional[str] = None
_current_video_ids: list[str] = []


# ─── FastAPI App ─────────────────────────────────────────────────────────────-

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 TubeInsight API starting up...")
    yield
    logger.info("🛑 TubeInsight API shutting down...")


app = FastAPI(
    title="TubeInsight AI API",
    description="AI-powered YouTube comment intelligence platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_video(request: AnalyzeRequest):
    """
    Analyze a YouTube video using the full LangGraph agent pipeline.
    
    Returns sentiment analysis, top comments, channel insights,
    agent summaries, and video metadata.
    """
    global _current_video_id, _current_video_ids
    
    # Extract video ID from URL
    yt = YouTubeClient()
    video_id = yt.extract_video_id(request.youtube_url)
    
    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Could not extract video ID from URL. Please provide a valid YouTube URL."
        )
    
    # Run the pipeline
    try:
        pipeline = TubeInsightPipeline()
        result = pipeline.analyze_video(
            video_url=request.youtube_url,
            video_id=video_id,
            max_comments=100,  # Default for API
        )
    except Exception as e:
        logger.exception("Pipeline analysis failed")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
    
    if result["status"] != "complete":
        errors = result.get("errors", ["Unknown error"])
        raise HTTPException(
            status_code=500,
            detail=f"Analysis incomplete: {'; '.join(errors)}"
        )
    
    # Store video_id for RAG context
    _current_video_id = video_id
    _current_video_ids = [video_id]
    
    # Extract sentiment data
    sentiment_result = result.get("sentiment_result", {})
    sentiment = {
        "label": sentiment_result.get("overall_sentiment", "neutral"),
        "score": sentiment_result.get("sentiment_score", 0.0),
        "vibe_score": sentiment_result.get("vibe_score", 5),
        "likeness_score": sentiment_result.get("likeness_score", 5),
        "toxicity_level": sentiment_result.get("toxicity_level", "unknown"),
    }
    
    # Extract top comments (top praised/liked comments)
    clean_comments = result.get("clean_comments", [])
    # Sort by like_count and take top 10
    sorted_comments = sorted(
        clean_comments,
        key=lambda x: x.get("like_count", 0),
        reverse=True
    )
    top_comments = [c["text"] for c in sorted_comments[:10]]
    
    # Extract channel insights from metadata
    metadata = result.get("video_metadata", {})
    channel_insights = {
        "subscriber_count": 0,  # Not directly available from video metadata
        "avg_views": metadata.get("view_count", 0),
        "engagement_rate": 0.0,  # Would need more data for accurate calculation
        "channel_name": metadata.get("channel_name", "Unknown"),
        "channel_id": metadata.get("channel_id", ""),
    }
    
    # Agent summaries from report and individual agents
    report = result.get("report", "")
    topic_result = result.get("topic_result", {})
    topics = topic_result.get("topics", [])
    
    agent_summaries = {
        "data_agent": f"Processed {len(clean_comments)} comments from video '{metadata.get('title', 'Unknown')}'",
        "sentiment_agent": sentiment_result.get("summary", "Sentiment analysis completed."),
        "topic_agent": f"Identified {len(topics)} key themes in viewer discussions.",
        "report_agent": report[:500] + "..." if len(report) > 500 else report,
    }
    
    # Video metadata
    video_metadata = {
        "title": metadata.get("title", "Unknown"),
        "views": metadata.get("view_count", 0),
        "likes": metadata.get("like_count", 0),
        "duration": "Unknown",  # Not directly available in current metadata
        "thumbnail": metadata.get("thumbnail", ""),
        "published_at": metadata.get("published_at", ""),
        "video_id": video_id,
        "url": metadata.get("url", f"https://youtube.com/watch?v={video_id}"),
    }
    
    return {
        "sentiment": sentiment,
        "top_comments": top_comments,
        "channel_insights": channel_insights,
        "agent_summaries": agent_summaries,
        "video_metadata": video_metadata,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the RAG agent about the analyzed video(s).
    
    Requires a video to have been analyzed first via /analyze.
    """
    global _current_video_ids
    
    if not _current_video_ids:
        raise HTTPException(
            status_code=400,
            detail="No video has been analyzed yet. Please call /analyze first."
        )
    
    try:
        agent = RAGAgent()
        answer = agent.chat(
            question=request.query,
            video_ids=_current_video_ids,
        )
        return {"response": answer}
    except Exception as e:
        logger.exception("RAG chat failed")
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


# ─── Main Entry Point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
