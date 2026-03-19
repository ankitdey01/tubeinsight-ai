"""
frontend/app.py
────────────────
TubeInsight AI — Main Streamlit Entry Point.
"""
print(f"[LOADING] {__file__}")

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.ollama_startup import ensure_ollama_ready

# Ensure Ollama is running before starting the app
ensure_ollama_ready()

import streamlit as st

st.set_page_config(
    page_title="TubeInsight AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark theme tweaks */
    .main { background-color: #0e1117; }
    .metric-card {
        background: #1e2130;
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #2d3250;
        margin-bottom: 1rem;
    }
    .vibe-score {
        font-size: 3rem;
        font-weight: 800;
        color: #00d4aa;
    }
    .tag {
        display: inline-block;
        background: #2d3250;
        color: #a0b4ff;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 0.2rem;
    }
    .stChatMessage { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.shields.io/badge/TubeInsight-AI-red?style=for-the-badge&logo=youtube")
    st.markdown("---")
    st.markdown("### 🎯 Navigation")
    st.page_link("app.py", label="🏠 Home", icon="🏠")
    st.page_link("pages/01_channel_view.py", label="📺 Channel Analysis")
    st.page_link("pages/02_video_analysis.py", label="🎬 Video Analysis")
    st.page_link("pages/03_ai_chat.py", label="🤖 AI Chat")
    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    max_comments = st.slider("Max comments per video", 100, 500, 300, step=50)
    st.session_state["max_comments"] = max_comments

# ─── Home Page ────────────────────────────────────────────────────────────────
st.title("🎯 TubeInsight AI")
st.markdown("### AI-powered audience intelligence for YouTube creators")
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    #### 📺 Channel Analysis
    Drop your channel URL and get sentiment trends,
    vibe scores, and AI insights across your latest 10 videos.
    """)
    if st.button("Analyze Channel →", width="stretch"):
        st.switch_page("pages/01_channel_view.py")

with col2:
    st.markdown("""
    #### 🎬 Video Analysis
    Deep-dive into a single video. Get sentiment breakdown,
    topic clusters, and a full AI-written insight report.
    """)
    if st.button("Analyze Video →", width="stretch"):
        st.switch_page("pages/02_video_analysis.py")

with col3:
    st.markdown("""
    #### 🤖 AI Chat
    Ask anything about your audience. The RAG-powered
    chatbot answers from your actual comment data.
    """)
    if st.button("Start Chatting →", width="stretch"):
        st.switch_page("pages/03_ai_chat.py")

st.markdown("---")
st.caption("Built with LLM API · LangGraph · ChromaDB · Streamlit")
