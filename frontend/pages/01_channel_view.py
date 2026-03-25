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
st.markdown("Analyze your latest videos and discover cross-video trends.")

# ─── Initialize Session State ─────────────────────────────────────────────────
if "channel_videos" not in st.session_state:
    st.session_state.channel_videos = None
if "channel_name" not in st.session_state:
    st.session_state.channel_name = None
if "channel_analysis_done" not in st.session_state:
    st.session_state.channel_analysis_done = False
if "channel_results" not in st.session_state:
    st.session_state.channel_results = None

# ─── Input ────────────────────────────────────────────────────────────────────
channel_url = st.text_input(
    "YouTube Channel URL",
    placeholder="https://youtube.com/@channelname  or  https://youtube.com/channel/UC...",
)

col1, col2 = st.columns([3, 1])
with col1:
    analyze_btn = st.button("🔍 Fetch Channel Videos", type="primary")
with col2:
    if st.button("🔄 Reset"):
        st.session_state.channel_videos = None
        st.session_state.channel_name = None
        st.session_state.channel_analysis_done = False
        st.session_state.channel_results = None
        st.rerun()

# ─── Fetch Videos Phase ───────────────────────────────────────────────────────
if analyze_btn and channel_url:
    from backend.core.youtube_client import YouTubeClient

    yt = YouTubeClient()
    channel_id = yt.extract_channel_id(channel_url)

    if not channel_id:
        st.error("❌ Could not resolve channel ID. Try a @handle or /channel/ URL.")
        st.stop()

    with st.spinner("Fetching channel videos..."):
        videos = yt.get_channel_videos(channel_id)

    if videos:
        st.session_state.channel_videos = videos
        st.session_state.channel_name = videos[0]['channel_name']
        st.session_state.channel_analysis_done = False
        st.session_state.channel_results = None
        st.rerun()
    else:
        st.error("❌ No videos found for this channel.")
        st.stop()

# ─── Video Selection Phase ────────────────────────────────────────────────────
if st.session_state.channel_videos and not st.session_state.channel_analysis_done:
    videos = st.session_state.channel_videos

    st.success(f"Found **{len(videos)} videos** for **{st.session_state.channel_name}**")
    st.markdown("### Select videos to analyze:")
    st.caption("💡 For channel analysis, each video is limited to 100 random comments for faster processing.")

    # Use form to prevent rerun on checkbox change
    with st.form("video_selection_form"):
        selected_videos = []
        cols = st.columns(2)

        for i, video in enumerate(videos):
            with cols[i % 2]:
                title_display = f"{video['title'][:55]}..." if len(video["title"]) > 55 else video["title"]
                checked = st.checkbox(
                    title_display,
                    value=True,
                    key=f"select_{video['video_id']}",
                )
                if checked:
                    selected_videos.append(video)

        submit_btn = st.form_submit_button(
            "▶ Start Analysis",
            type="primary",
            use_container_width=True,
        )

    if submit_btn and selected_videos:
        # Lazy imports
        from backend.agents.orchestrator import TubeInsightPipeline
        from config.settings import get_settings

        pipeline = TubeInsightPipeline()
        # Limit to 100 comments per video for channel analysis (faster)
        max_comments = 100

        all_results = []
        progress_bar = st.progress(0, text="Starting analysis...")

        for i, video in enumerate(selected_videos):
            vid_id = video["video_id"]
            video_url = f"https://youtube.com/watch?v={vid_id}"
            progress_bar.progress(
                (i) / len(selected_videos),
                text=f"Analyzing: {video['title'][:40]}..."
            )

            try:
                result = pipeline.analyze_video(
                    video_url=video_url,
                    video_id=vid_id,
                    max_comments=max_comments,
                )
                if result["status"] == "complete":
                    all_results.append(result)
                else:
                    st.warning(f"⚠️ Analysis incomplete for: {video['title'][:40]}...")
            except Exception as e:
                st.error(f"❌ Failed to analyze: {video['title'][:40]}... ({str(e)[:50]})")

            progress_bar.progress((i + 1) / len(selected_videos))

        progress_bar.empty()

        if all_results:
            st.session_state.channel_results = all_results
            st.session_state.channel_analysis_done = True
            st.session_state.current_video_ids = [r["video_metadata"]["video_id"] for r in all_results]
            st.rerun()
        else:
            st.error("❌ No videos were successfully analyzed.")

# ─── Results Display Phase ────────────────────────────────────────────────────
if st.session_state.channel_analysis_done and st.session_state.channel_results:
    import plotly.graph_objects as go

    all_results = st.session_state.channel_results

    st.success(f"✅ Analyzed **{len(all_results)} videos** for **{st.session_state.channel_name}**")

    # ─── Cross-Video Sentiment Chart ──────────────────────────────────────────
    st.markdown("### 📈 Sentiment Trend Across Videos")

    titles = [r["video_metadata"]["title"][:25] + "..." for r in all_results]
    vibe_scores = [r["sentiment_result"].get("vibe_score", 0) for r in all_results]
    likeness_scores = [r["sentiment_result"].get("likeness_score", 0) for r in all_results]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=titles, y=vibe_scores,
        name="Vibe Score",
        line=dict(color="#00d4aa", width=3),
        mode="lines+markers"
    ))
    fig.add_trace(go.Scatter(
        x=titles, y=likeness_scores,
        name="Likeness Score",
        line=dict(color="#a0b4ff", width=3),
        mode="lines+markers"
    ))
    fig.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font_color="white",
        yaxis=dict(range=[0, 10], title="Score"),
        xaxis_tickangle=-30,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=40, r=40, t=60, b=100),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ─── Channel Overview Metrics ─────────────────────────────────────────────
    st.markdown("### 📊 Channel Overview")

    avg_vibe = sum(vibe_scores) / len(vibe_scores) if vibe_scores else 0
    avg_likeness = sum(likeness_scores) / len(likeness_scores) if likeness_scores else 0

    # Count sentiment distribution
    sentiments = [r["sentiment_result"].get("overall_sentiment", "neutral") for r in all_results]
    positive_count = sum(1 for s in sentiments if s == "positive")
    negative_count = sum(1 for s in sentiments if s == "negative")
    neutral_count = sum(1 for s in sentiments if s in ["neutral", "mixed"])

    total_comments = sum(r["sentiment_result"].get("comments_analyzed", 0) for r in all_results)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Avg Vibe", f"{avg_vibe:.1f}/10")
    c2.metric("Avg Likeness", f"{avg_likeness:.1f}/10")
    c3.metric("Positive Videos", f"{positive_count}/{len(all_results)}")
    c4.metric("Negative Videos", f"{negative_count}/{len(all_results)}")
    c5.metric("Comments Analyzed", f"{total_comments}")

    # ─── Common Themes Across Videos ──────────────────────────────────────────
    st.markdown("### 🎯 Common Themes Across Videos")

    # Aggregate top praises, criticisms, questions
    all_praises = []
    all_criticisms = []
    all_questions = []

    for r in all_results:
        sent = r.get("sentiment_result", {})
        all_praises.extend(sent.get("top_praises", []))
        all_criticisms.extend(sent.get("top_criticisms", []))
        all_questions.extend(sent.get("top_questions", []))

    # Dedupe and take top items
    unique_praises = list(dict.fromkeys(all_praises))[:5]
    unique_criticisms = list(dict.fromkeys(all_criticisms))[:5]
    unique_questions = list(dict.fromkeys(all_questions))[:5]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**✅ Top Praises**")
        for praise in unique_praises:
            st.markdown(f"- {praise}")
        if not unique_praises:
            st.caption("No praises collected")

    with col2:
        st.markdown("**⚠️ Top Criticisms**")
        for criticism in unique_criticisms:
            st.markdown(f"- {criticism}")
        if not unique_criticisms:
            st.caption("No criticisms collected")

    with col3:
        st.markdown("**❓ Top Questions**")
        for question in unique_questions:
            st.markdown(f"- {question}")
        if not unique_questions:
            st.caption("No questions collected")

    # ─── Video Summary Cards ──────────────────────────────────────────────────
    st.markdown("### 🎬 Video-by-Video Summary")

    for result in all_results:
        meta = result["video_metadata"]
        sent = result["sentiment_result"]
        topics = result.get("topic_result", {}).get("topics", [])

        with st.expander(f"**{meta['title']}**", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Vibe", f"{sent.get('vibe_score', 'N/A')}/10")
            c2.metric("Likeness", f"{sent.get('likeness_score', 'N/A')}/10")
            c3.metric("Sentiment", str(sent.get("overall_sentiment", "N/A")).capitalize())
            toxicity = sent.get("toxicity_level", "N/A")
            c4.metric("Toxicity", str(toxicity).capitalize() if toxicity else "N/A")

            st.markdown(f"**Summary:** {sent.get('summary', 'N/A')}")

            if topics:
                st.markdown("**Topics:**")
                topic_labels = [t.get("label", "Unknown") for t in topics[:4]]
                st.markdown(" • ".join(topic_labels))

            st.markdown(f"[🔗 Watch Video]({meta.get('url', '')})")

    st.markdown("---")
    st.info("💬 Head to **AI Chat** to ask questions across all analyzed videos!")
