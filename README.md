# 🎯 TubeInsight AI

> **AI-powered YouTube comment intelligence platform** — built for creators who want to truly understand their audience.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-green)](https://github.com/langchain-ai/langgraph)
[![LLM](https://img.shields.io/badge/LLM-OpenRouter%20%7C%20Ollama-orange)](https://openrouter.ai/)
[![Streamlit](https://img.shields.io/badge/frontend-Streamlit-red)](https://streamlit.io/)

---

## 🧠 What Is This?

TubeInsight AI is a creator intelligence dashboard that transforms raw YouTube comment data into structured, actionable insight using:

- **Multi-agent AI orchestration** via LangGraph
- **RAG-powered chatbot** — ask natural questions about your audience
- **Sentiment + vibe analysis** per video and across your channel
- **Topic clustering** to surface what viewers actually care about
- **AI-generated insight reports** per video

---

## 🗂️ Project Structure

```
tubeinsight-ai/
├── frontend/                   # Streamlit UI
│   ├── app.py                  # Main entry point
│   ├── pages/                  # Multi-page Streamlit
│   │   ├── 01_channel_view.py
│   │   ├── 02_video_analysis.py
│   │   └── 03_ai_chat.py
│   └── components/             # Reusable UI components
│       ├── charts.py
│       ├── metrics.py
│       └── sidebar.py
│
├── backend/
│   ├── agents/                 # LangGraph agents
│   │   ├── orchestrator.py     # Master agent router
│   │   ├── data_agent.py       # YouTube data ingestion
│   │   ├── sentiment_agent.py  # Emotion + vibe scoring
│   │   ├── topic_agent.py      # Comment clustering
│   │   ├── rag_agent.py        # RAG chat interface
│   │   └── report_agent.py     # Insight report generation
│   │
│   ├── core/                   # Core business logic
│   │   ├── youtube_client.py   # YouTube API wrapper
│   │   ├── embeddings.py       # Embedding pipeline
│   │   ├── vectorstore.py      # ChromaDB interface
│   │   └── llm_client.py       # OpenRouter / Ollama wrapper
│   │
│   ├── api/                    # FastAPI layer (optional, for decoupling)
│   │   ├── main.py
│   │   ├── routes/
│   │   └── schemas.py
│   │
│   └── utils/
│       ├── preprocessing.py    # Comment cleaning
│       ├── cache.py            # Redis / pickle cache
│       └── logger.py
│
├── data/
│   ├── raw/                    # Raw API responses (JSON)
│   ├── processed/              # Cleaned comment DataFrames
│   └── vectorstore/            # ChromaDB persistent storage
│
├── config/
│   ├── settings.py             # Pydantic settings
│   └── prompts.py              # All LLM prompt templates
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── scripts/
│   ├── ingest_channel.py       # CLI: ingest a channel
│   └── ingest_video.py         # CLI: ingest a single video
│
├── docs/
│   └── architecture.md
│
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## ⚡ Quickstart

```bash
# 1. Clone and setup
git clone https://github.com/yourname/tubeinsight-ai
cd tubeinsight-ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Fill in: YOUTUBE_API_KEY and OPENROUTER_API_KEY
# Or set OLLAMA_BASE_URL to use a local model instead

# 4. Run the app
streamlit run frontend/app.py
```

---

## 🤖 Agent Architecture

```
User Input (channel URL / video URL)
        │
        ▼
  Orchestrator Agent  (LangGraph StateGraph)
        │
   ┌────┼────┬────────┬──────────┐
   ▼    ▼    ▼        ▼          ▼
 Data  Sent Topic    RAG       Report
Agent  Agent Agent   Agent     Agent
```

| Agent | Responsibility |
|---|---|
| `DataAgent` | Fetch comments + metadata via YouTube API |
| `SentimentAgent` | Score emotion, toxicity, hype, likeness |
| `TopicAgent` | Cluster comments into themes via embeddings |
| `RAGAgent` | Answer creator questions about their content |
| `ReportAgent` | Generate the final written insight summary |

---

## 🔑 Environment Variables

```env
YOUTUBE_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
OLLAMA_BASE_URL=http://localhost:11434  # Optional alternative to OpenRouter
CHROMA_PERSIST_DIR=./data/vectorstore
CACHE_DIR=./data/processed
MAX_COMMENTS_PER_VIDEO=500
```

---

## 📦 Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Streamlit |
| Agent Orchestration | LangGraph |
| LLM | OpenRouter or local Ollama |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` |
| Vector DB | ChromaDB |
| YouTube Data | YouTube Data API v3 |
| Sentiment Baseline | VADER + LLM refinement |
| Topic Modeling | BERTopic / KMeans |
| API Layer | FastAPI |
| Caching | diskcache |
| Config | Pydantic Settings |
