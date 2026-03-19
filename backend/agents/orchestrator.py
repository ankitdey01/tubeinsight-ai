"""
backend/agents/orchestrator.py
────────────────────────────────
LangGraph StateGraph orchestrator.
Defines the full pipeline as a graph of agent nodes.

Flow:
  START → data_agent → sentiment_agent → topic_agent → report_agent → END

RAG agent is invoked on-demand separately (not part of ingestion pipeline).
"""
print(f"[LOADING] {__file__}")

from typing import TypedDict, Annotated, Optional
import operator
from loguru import logger

from langgraph.graph import StateGraph, END, START

# Ensure Ollama is running when orchestrator is imported
from backend.core.ollama_startup import ensure_ollama_ready
ensure_ollama_ready()

from backend.agents.data_agent import DataAgent
from backend.agents.sentiment_agent import SentimentAgent
from backend.agents.topic_agent import TopicAgent
from backend.agents.report_agent import ReportAgent


# ─── State Schema ─────────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    """Shared state passed between all agent nodes."""
    # Input
    video_id: str
    video_url: str
    max_comments: Optional[int]

    # Data Agent output
    video_metadata: Optional[dict]
    raw_comments: Optional[list[dict]]
    clean_comments: Optional[list[dict]]

    # Sentiment Agent output
    sentiment_result: Optional[dict]

    # Topic Agent output
    topic_result: Optional[dict]

    # Report Agent output
    report: Optional[str]

    # Error tracking
    errors: Annotated[list[str], operator.add]
    status: str  # "running" | "complete" | "failed"


# ─── Agent Node Wrappers ───────────────────────────────────────────────────────

def run_data_agent(state: PipelineState) -> dict:
    logger.info("▶ DataAgent: Fetching video data...")
    try:
        agent = DataAgent()
        # Always force refresh to ensure data is stored for RAG
        result = agent.run(
            video_id=state["video_id"],
            force_refresh=True,
            max_comments=state.get("max_comments"),
        )
        # Ensure clean_comments is always a list
        clean_comments = result.get("clean_comments", [])
        if not isinstance(clean_comments, list):
            clean_comments = []
        return {
            "video_metadata": result.get("metadata"),
            "raw_comments": result.get("raw_comments", []),
            "clean_comments": clean_comments,
            "status": "data_complete",
        }
    except Exception as e:
        logger.error(f"DataAgent failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"errors": [f"DataAgent: {str(e)}"], "status": "failed"}


def run_sentiment_agent(state: PipelineState) -> dict:
    logger.info("▶ SentimentAgent: Analyzing sentiment...")
    if state.get("status") == "failed":
        return {}
    try:
        agent = SentimentAgent()
        result = agent.run(
            comments=state["clean_comments"],
            video_title=state["video_metadata"]["title"],
        )
        return {"sentiment_result": result, "status": "sentiment_complete"}
    except Exception as e:
        logger.error(f"SentimentAgent failed: {e}")
        return {"errors": [f"SentimentAgent: {str(e)}"], "status": "failed"}


def run_topic_agent(state: PipelineState) -> dict:
    logger.info("▶ TopicAgent: Clustering topics...")
    if state.get("status") == "failed":
        return {}
    try:
        agent = TopicAgent()
        result = agent.run(
            video_id=state["video_id"],
            comments=state["clean_comments"],
            video_title=state["video_metadata"]["title"],
        )
        return {"topic_result": result, "status": "topics_complete"}
    except Exception as e:
        logger.error(f"TopicAgent failed: {e}")
        return {"errors": [f"TopicAgent: {str(e)}"], "status": "failed"}


def run_report_agent(state: PipelineState) -> dict:
    logger.info("▶ ReportAgent: Generating insight report...")
    if state.get("status") == "failed":
        return {}
    try:
        agent = ReportAgent()
        report = agent.run(
            video_metadata=state["video_metadata"],
            sentiment=state["sentiment_result"],
            topics=state["topic_result"],
            total_comments=len(state["clean_comments"]),
        )
        return {"report": report, "status": "complete"}
    except Exception as e:
        logger.error(f"ReportAgent failed: {e}")
        return {"errors": [f"ReportAgent: {str(e)}"], "status": "failed"}


# ─── Graph Construction ───────────────────────────────────────────────────────

def build_pipeline() -> StateGraph:
    """Build and return the compiled LangGraph pipeline."""
    graph = StateGraph(PipelineState)

    # Register nodes
    graph.add_node("data_agent", run_data_agent)
    graph.add_node("sentiment_agent", run_sentiment_agent)
    graph.add_node("topic_agent", run_topic_agent)
    graph.add_node("report_agent", run_report_agent)

    # Define edges (sequential pipeline)
    graph.add_edge(START, "data_agent")
    graph.add_edge("data_agent", "sentiment_agent")
    graph.add_edge("sentiment_agent", "topic_agent")
    graph.add_edge("topic_agent", "report_agent")
    graph.add_edge("report_agent", END)

    return graph.compile()


# ─── Public Interface ─────────────────────────────────────────────────────────

class TubeInsightPipeline:
    def __init__(self):
        self.pipeline = build_pipeline()

    def analyze_video(
        self,
        video_url: str,
        video_id: str,
        max_comments: int | None = None,
    ) -> PipelineState:
        """Run the full analysis pipeline for a single video."""
        logger.info(f"🚀 Starting TubeInsight pipeline for {video_id}")

        initial_state: PipelineState = {
            "video_id": video_id,
            "video_url": video_url,
            "max_comments": max_comments,
            "video_metadata": None,
            "raw_comments": None,
            "clean_comments": None,
            "sentiment_result": None,
            "topic_result": None,
            "report": None,
            "errors": [],
            "status": "running",
        }

        final_state = self.pipeline.invoke(initial_state)

        if final_state["status"] == "complete":
            logger.success(f"✅ Pipeline complete for {video_id}")
        else:
            logger.error(f"❌ Pipeline failed: {final_state['errors']}")

        return final_state
