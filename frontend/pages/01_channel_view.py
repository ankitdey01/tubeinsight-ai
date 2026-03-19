"""
frontend/pages/01_channel_view.py
Channel-level analysis page — latest 10 videos overview.
"""
print(f"[LOADING] {__file__}")

import streamlit as st
import sys
sys.path.append(".")

st.set_page_config(page_title="Channel Analysis · TubeInsight", page_icon="📺", layout="wide")
st.title("📺 Channel Analysis")
st.markdown("Analyze your latest 10 videos and discover cross-video trends.")

# ─── Input ────────────────────────────────────────────────────────────────────
channel_url = st.text_input(
    "YouTube Channel URL",
    placeholder="https://youtube.com/@channelname  or  https://youtube.com/channel/UC...",
)

analyze_btn = st.button("🚀 Analyze Channel", type="primary", width="stretch")

if analyze_btn and channel_url:
    # Lazy imports - only load when analysis is triggered
    import plotly.graph_objects as go
    from backend.core.youtube_client import YouTubeClient
    from backend.agents.orchestrator import TubeInsightPipeline
    from config.settings import get_settings
    
    yt = YouTubeClient()
    channel_id = yt.extract_channel_id(channel_url)

    if not channel_id:
        st.error("❌ Could not resolve channel ID. Try a @handle or /channel/ URL.")
        st.stop()

    # ─── Fetch videos ─────────────────────────────────────────────────────────
    with st.spinner("Fetching channel videos..."):
        videos = yt.get_channel_videos(channel_id)

    st.success(f"Found **{len(videos)} videos** for **{videos[0]['channel_name']}**")

    # Show video list with checkboxes (user can deselect)
    st.markdown("### Select videos to analyze:")
    selected_ids = []
    cols = st.columns(2)
    for i, video in enumerate(videos):
        with cols[i % 2]:
            checked = st.checkbox(
                f"**{video['title'][:60]}...**" if len(video["title"]) > 60 else video["title"],
                value=True,
                key=f"video_{video['video_id']}",
            )
            if checked:
                selected_ids.append(video["video_id"])

    run_analysis = st.button(
        f"▶ Analyze {len(selected_ids)} Selected Videos",
        type="primary",
        disabled=len(selected_ids) == 0,
    )

    if run_analysis and selected_ids:
        pipeline = TubeInsightPipeline()
        max_comments = int(st.session_state.get("max_comments", get_settings().max_comments_per_video))
        all_results = []
        progress_bar = st.progress(0)

        for i, vid_id in enumerate(selected_ids):
            video_url = f"https://youtube.com/watch?v={vid_id}"
            with st.spinner(f"Analyzing video {i+1}/{len(selected_ids)}..."):
                result = pipeline.analyze_video(
                    video_url=video_url,
                    video_id=vid_id,
                    max_comments=max_comments,
                )
                if result["status"] == "complete":
                    all_results.append(result)
            progress_bar.progress((i + 1) / len(selected_ids))

        st.session_state["current_video_ids"] = [r["video_metadata"]["video_id"] for r in all_results]
        st.session_state["channel_results"] = all_results

        progress_bar.empty()

        # ─── Cross-Video Sentiment Chart ──────────────────────────────────────
        st.markdown("### 📈 Sentiment Trend Across Videos")

        titles = [r["video_metadata"]["title"][:30] + "..." for r in all_results]
        vibe_scores = [r["sentiment_result"].get("vibe_score", 0) for r in all_results]
        likeness_scores = [r["sentiment_result"].get("likeness_score", 0) for r in all_results]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=titles, y=vibe_scores, name="Vibe Score", line=dict(color="#00d4aa", width=3)))
        fig.add_trace(go.Scatter(x=titles, y=likeness_scores, name="Likeness Score", line=dict(color="#a0b4ff", width=3)))
        fig.update_layout(
            paper_bgcolor="#0e1117",
            font_color="white",
            yaxis=dict(range=[0, 10]),
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig, width="stretch")

        # ─── Video Summary Cards ──────────────────────────────────────────────
        st.markdown("### 🎬 Video-by-Video Summary")
        for result in all_results:
            meta = result["video_metadata"]
            sent = result["sentiment_result"]
            with st.expander(f"**{meta['title']}**", expanded=False):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Vibe", f"{sent.get('vibe_score', 'N/A')}/10")
                c2.metric("Likeness", f"{sent.get('likeness_score', 'N/A')}/10")
                c3.metric("Sentiment", sent.get("overall_sentiment", "N/A").capitalize())
                c4.metric("Toxicity", sent.get("toxicity_level", "N/A").capitalize())
                st.markdown(f"**Summary:** {sent.get('summary', 'N/A')}")

        st.success("✅ Channel analysis complete! Head to **AI Chat** to ask questions across all videos.")
