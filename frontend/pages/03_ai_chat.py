"""
frontend/pages/03_ai_chat.py
RAG-powered AI chat page.
Creators can ask natural language questions about their comment data.
"""
print(f"[LOADING] {__file__}")

import streamlit as st
import sys
sys.path.append(".")

st.set_page_config(page_title="AI Chat · TubeInsight", page_icon="🤖", layout="wide")
st.title("🤖 Ask Your Audience")
st.markdown("Chat with an AI that has read all your comments. Ask anything.")

# ─── Check for analyzed content ───────────────────────────────────────────────
video_ids = st.session_state.get("current_video_ids", [])

if not video_ids:
    # If the session is new, recover using already indexed videos from storage.
    from backend.core.vectorstore import VectorStore

    indexed_video_ids = VectorStore().list_indexed_video_ids()
    if indexed_video_ids:
        st.session_state["current_video_ids"] = indexed_video_ids
        video_ids = indexed_video_ids
        st.info(f"Using {len(video_ids)} indexed video(s) already available in your comment store.")
    else:
        st.warning("⚠️ No video analyzed yet. Go to **Video Analysis** or **Channel Analysis** first.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Go to Video Analysis"):
                st.switch_page("pages/02_video_analysis.py")
        with col2:
            if st.button("Go to Channel Analysis"):
                st.switch_page("pages/01_channel_view.py")
        st.stop()

scope = "channel" if len(video_ids) > 1 else "video"
st.caption(f"💡 Answering from **{len(video_ids)} {scope}** comment data | {sum(1 for _ in video_ids)} source(s) indexed")

# ─── Suggested Questions ──────────────────────────────────────────────────────
st.markdown("#### 💡 Try asking:")
suggested = [
    "What do my viewers love most about this content?",
    "What are the most common complaints in the comments?",
    "What topics do my viewers keep asking me to cover?",
    "Which video got the most negative feedback and why?",
    "What's the overall vibe of my audience?",
]

cols = st.columns(3)
for i, q in enumerate(suggested[:3]):
    with cols[i]:
        if st.button(q, key=f"suggest_{i}"):
            st.session_state["prefill_question"] = q

st.markdown("---")

# ─── Chat Interface ───────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

current_scope = tuple(video_ids)
if st.session_state.get("chat_scope_video_ids") != current_scope:
    st.session_state["chat_scope_video_ids"] = current_scope
    st.session_state["chat_history"] = []

# Display chat history
for msg in st.session_state["chat_history"]:
    with st.chat_message(msg["role"], avatar="🎬" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

# Input
prefill = st.session_state.pop("prefill_question", "")
user_input = st.chat_input("Ask about your audience...", key="chat_input")
if prefill and not user_input:
    user_input = prefill

if user_input:
    # Lazy import - only load when chat is triggered
    from backend.agents.rag_agent import RAGAgent
    
    # Show user message
    with st.chat_message("user", avatar="🎬"):
        st.markdown(user_input)

    st.session_state["chat_history"].append({"role": "user", "content": user_input})

    # Generate response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Searching through your comments..."):
            try:
                agent = RAGAgent()
                answer = agent.chat(
                    question=user_input,
                    video_ids=video_ids,
                )
            except Exception as e:
                answer = (
                    "I hit an error while searching your analyzed comments. "
                    "Please re-run analysis and try again."
                )
                st.caption(f"Error details: {e}")

        st.markdown(answer)

    # Update display history
    st.session_state["chat_history"].append({"role": "assistant", "content": answer})

# ─── Clear chat ───────────────────────────────────────────────────────────────
if st.session_state["chat_history"]:
    if st.button("🗑️ Clear Chat"):
        st.session_state["chat_history"] = []
        st.rerun()
