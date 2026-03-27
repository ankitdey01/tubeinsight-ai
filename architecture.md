# TubeInsight AI — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT FRONTEND                        │
│                                                                   │
│  app.py (home)                                                   │
│  ├── pages/01_channel_view.py    → Channel-level dashboard       │
│  ├── pages/02_video_analysis.py  → Single video deep-dive        │
│  └── pages/03_ai_chat.py         → RAG chatbot interface         │
└────────────────────────────┬────────────────────────────────────┘
                             │ calls
┌────────────────────────────▼────────────────────────────────────┐
│                    LANGGRAPH ORCHESTRATOR                         │
│               backend/agents/orchestrator.py                     │
│                                                                   │
│  StateGraph:                                                      │
│  START → DataAgent → SentimentAgent → TopicAgent → ReportAgent → END
└──┬──────────┬──────────┬──────────┬────────────────────────────┘
   │          │          │          │
┌──▼──┐  ┌───▼───┐  ┌───▼────┐  ┌──▼──────┐  ┌──────────┐
│Data │  │Sentiment│  │Topic   │  │Report   │  │RAG       │
│Agent│  │Agent    │  │Agent   │  │Agent    │  │Agent     │
│     │  │         │  │        │  │         │  │(on-demand│
│YT   │  │VADER +  │  │KMeans  │  │Claude   │  │ for chat)│
│API  │  │Claude   │  │+Claude │  │synthesis│  │          │
└──┬──┘  └─────────┘  └────────┘  └─────────┘  └────┬─────┘
   │                                                  │
┌──▼──────────────────────────────────────────────────▼─────────┐
│                       CORE LAYER                                │
│                                                                  │
│  youtube_client.py  → YouTube Data API v3                       │
│  llm_client.py      → OpenRouter API or local Ollama            │
│  embeddings.py      → Local sentence-transformers               │
│  vectorstore.py     → ChromaDB (persistent local)               │
└────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Ingestion Pipeline (per video)
1. `YouTubeClient.get_video_metadata()` → video title, stats, etc.
2. `YouTubeClient.get_video_comments()` → raw comment objects
3. `preprocess_comments()` → filter spam, clean text
4. `EmbeddingClient.embed_texts()` → float vectors
5. `VectorStore.upsert_comments()` → stored in ChromaDB

### Analysis Pipeline
6. `SentimentAgent.run()` → VADER baseline + LLM qualitative analysis
7. `TopicAgent.run()` → KMeans clusters + LLM labeling
8. `ReportAgent.run()` → Final written report

### RAG Chat (on-demand)
1. User asks a question
2. `EmbeddingClient.embed_query()` → question vector
3. `VectorStore.query()` → top-K most relevant comments
4. The configured LLM generates a grounded answer from retrieved context

## Key Design Decisions

**Why LangGraph?**
State machines are more reliable than simple chains for production pipelines.
Each agent is isolated and its output is type-checked via TypedDict state.

**Why KMeans over BERTopic?**
BERTopic is powerful but complex to tune. KMeans on normalized local
sentence-transformer embeddings gives excellent results with controllable
cluster counts.

**Why VADER + LLM (not just LLM)?**
VADER is free and fast — it processes ALL comments instantly.
LLM analysis is reserved for a smart sample (top 100 by likes),
keeping costs low while maximizing insight quality.

**Why per-video ChromaDB collections?**
Isolated collections = fast single-video queries + easy cache invalidation.
Channel-level RAG is done by querying multiple collections and merging.

## Cost Estimates (per video, ~300 comments)

| Step | Model | Estimated Cost |
|---|---|---|
| Embeddings (300 comments) | all-MiniLM-L6-v2 (local) | ~$0 |
| Sentiment analysis (100 comments) | Configured LLM | Depends on provider |
| Topic labeling | Configured LLM | Depends on provider |
| Report generation | Configured LLM | Depends on provider |
| **Total per video** | | **Embeddings stay local; LLM cost depends on provider** |

Full channel analysis cost depends on the selected LLM route.
