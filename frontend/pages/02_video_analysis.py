"""
frontend/pages/02_video_analysis.py
Single video deep-dive analysis page.
"""
print(f"[LOADING] {__file__}")

import streamlit as st
import sys
sys.path.append(".")

st.set_page_config(page_title="Video Analysis · TubeInsight", page_icon="🎬", layout="wide")
st.title("🎬 Video Analysis")
st.markdown("Deep-dive into any YouTube video's audience sentiment and topics.")

# ─── Input ────────────────────────────────────────────────────────────────────
video_url = st.text_input(
    "YouTube Video URL",
    placeholder="https://youtube.com/watch?v=...",
)

analyze_btn = st.button("🚀 Analyze Video", type="primary", width="stretch")

if analyze_btn and video_url:
    # Lazy imports - only load when analysis is triggered
    import plotly.graph_objects as go
    from backend.core.youtube_client import YouTubeClient
    from backend.agents.orchestrator import TubeInsightPipeline
    from config.settings import get_settings
    
    yt = YouTubeClient()
    video_id = yt.extract_video_id(video_url)

    if not video_id:
        st.error("❌ Could not extract video ID from URL. Please check the link.")
        st.stop()

    # ─── Run Pipeline ──────────────────────────────────────────────────────────
    max_comments = int(st.session_state.get("max_comments", get_settings().max_comments_per_video))
    with st.spinner("🤖 Agents running analysis... this takes ~30-60 seconds"):
        pipeline = TubeInsightPipeline()
        result = pipeline.analyze_video(
            video_url=video_url,
            video_id=video_id,
            max_comments=max_comments,
        )

    if result["status"] != "complete":
        st.error(f"Analysis failed: {result['errors']}")
        st.stop()

    # Save to session for AI Chat
    st.session_state["current_video_ids"] = [video_id]

    meta = result["video_metadata"]
    sentiment = result["sentiment_result"]
    topics = result["topic_result"]
    report = result["report"]

    # ─── Video Header ─────────────────────────────────────────────────────────
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"## {meta['title']}")
        st.caption(f"**{meta['channel_name']}** · {meta['view_count']:,} views · {meta['like_count']:,} likes")
        st.caption(f"[Open on YouTube ↗]({meta['url']})")
    with col2:
        if meta.get("thumbnail"):
            st.image(meta["thumbnail"], width="stretch")

    # ─── Top Metrics ──────────────────────────────────────────────────────────
    st.markdown("### 📊 Key Metrics")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Vibe Score", f"{sentiment.get('vibe_score', 'N/A')}/10")
    m2.metric("Likeness Score", f"{sentiment.get('likeness_score', 'N/A')}/10")
    m3.metric("Overall Sentiment", sentiment.get("overall_sentiment", "N/A").capitalize())
    m4.metric("Comments Analyzed", sentiment.get("comments_analyzed", 0))
    m5.metric("Toxicity Level", sentiment.get("toxicity_level", "N/A").capitalize())

    # ─── Sentiment Charts ─────────────────────────────────────────────────────
    st.markdown("### 💬 Sentiment Breakdown")
    c1, c2 = st.columns(2)

    with c1:
        # Primary: AI-powered sentiment distribution
        sentiment_dist = sentiment.get("sentiment_distribution", {})
        if sentiment_dist:
            labels = [k.capitalize() for k in sentiment_dist.keys()]
            values = list(sentiment_dist.values())
            colors = ["#00d4aa", "#FF4444", "#888888"]  # green, red, gray
            
            fig = go.Figure(go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker_colors=colors,
                textinfo="label+percent",
                textposition="outside",
            ))
            fig.update_layout(
                title="Comment Sentiment Distribution",
                showlegend=False,
                paper_bgcolor="#0e1117",
                font_color="white",
                margin=dict(t=60, b=30, l=30, r=30),
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No sentiment data available")

    with c2:
        # Secondary: Emotion breakdown (when available from LLM)
        emotions = sentiment.get("emotion_breakdown", {})
        has_real_emotions = emotions and any(v > 5 for k, v in emotions.items() if k != "neutral")
        
        if has_real_emotions:
            # Show emotion bar chart for better readability
            emotion_labels = [k.capitalize() for k in emotions.keys()]
            emotion_values = list(emotions.values())
            emotion_colors = ["#FFD700", "#FF69B4", "#FF4444", "#6699FF", "#FF9900", "#888888"]
            
            fig2 = go.Figure(go.Bar(
                x=emotion_labels,
                y=emotion_values,
                marker_color=emotion_colors,
            ))
            fig2.update_layout(
                title="Emotion Breakdown (%)",
                paper_bgcolor="#0e1117",
                font_color="white",
                yaxis_title="Percentage",
                xaxis_tickangle=-15,
                margin=dict(t=60, b=60, l=50, r=30),
            )
            st.plotly_chart(fig2, width="stretch")
        else:
            # Show sentiment score indicator
            score = sentiment.get("sentiment_score", 0)
            vibe = sentiment.get("vibe_score", 5)
            
            fig2 = go.Figure()
            
            # Sentiment score gauge
            fig2.add_trace(go.Indicator(
                mode="gauge+number",
                value=score,
                title={"text": "Sentiment Score", "font": {"color": "white"}},
                number={"font": {"color": "white"}},
                gauge={
                    "axis": {"range": [-1, 1], "tickcolor": "white"},
                    "bar": {"color": "#00d4aa" if score > 0 else "#FF4444"},
                    "bgcolor": "#1a1a1a",
                    "borderwidth": 2,
                    "bordercolor": "#333",
                    "steps": [
                        {"range": [-1, -0.3], "color": "#331111"},
                        {"range": [-0.3, 0.3], "color": "#333333"},
                        {"range": [0.3, 1], "color": "#113311"},
                    ],
                },
            ))
            fig2.update_layout(
                paper_bgcolor="#0e1117",
                font_color="white",
                margin=dict(t=60, b=30, l=30, r=30),
                height=250,
            )
            st.plotly_chart(fig2, width="stretch")
            
            # Vibe score text
            st.metric("Overall Vibe", f"{vibe}/10", delta=None)

    # ─── Topic Clusters ───────────────────────────────────────────────────────
    st.markdown("### 🗂️ Topic Clusters")
    topic_items = topics.get("topics", [])
    if topic_items:
        cols = st.columns(min(3, len(topic_items)))
        for i, topic in enumerate(topic_items[:6]):
            with cols[i % 3]:
                sentiment_color = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}.get(
                    topic.get("sentiment", "neutral"), "🟡"
                )
                st.markdown(f"""
                **{sentiment_color} {topic['label']}**
                _{topic['description']}_
                > {topic['representative_comments'][0] if topic.get('representative_comments') else ''}
                """)
                st.caption(f"{topic['size']} comments")
                st.markdown("---")

    # ─── Insights Lists ───────────────────────────────────────────────────────
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("### 👍 What They Loved")
        for item in sentiment.get("top_praises", []):
            st.markdown(f"- {item}")

    with col_b:
        st.markdown("### 👎 What Needs Work")
        for item in sentiment.get("top_criticisms", []):
            st.markdown(f"- {item}")

    with col_c:
        st.markdown("### ❓ Top Questions")
        for item in sentiment.get("top_questions", []):
            st.markdown(f"- {item}")

    # ─── AI Insight Report Cards ──────────────────────────────────────────────
    st.markdown("### 📋 AI Insight Report")
    st.caption("💡 Swipe through the cards below to explore your audience insights")
    
    # Extract data for cards
    overall = sentiment.get("overall_sentiment", "unknown")
    vibe = sentiment.get("vibe_score", 5)
    likeness = sentiment.get("likeness_score", 5)
    praises = sentiment.get("top_praises", [])
    criticisms = sentiment.get("top_criticisms", [])
    questions = sentiment.get("top_questions", [])
    topic_list = topics.get("topics", [])
    sentiment_dist = sentiment.get("sentiment_distribution", {})
    
    # Create swipeable tabs (cards)
    report_tabs = st.tabs(["📊 Summary", "❤️ Loved", "⚠️ Attention", "❓ Questions", "💡 Tips", "🔥 Vibe"])
    
    # Card 1: Executive Summary
    with report_tabs[0]:
        st.markdown("#### 📊 Executive Summary")
        
        # Key metrics in a row
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("📊 Sentiment", overall.capitalize())
        with m2:
            st.metric("🔥 Vibe", f"{vibe}/10")
        with m3:
            st.metric("❤️ Likeness", f"{likeness}/10")
        with m4:
            st.metric("💬 Comments", sentiment.get("comments_analyzed", 0))
        
        st.markdown("---")
        
        # Summary text
        st.markdown(f"""
        **Your video received {overall.upper()} sentiment** with a community vibe of **{vibe}/10**. 
        
        Viewers showed **{likeness}/10** likeness for the content based on {sentiment.get('comments_analyzed', 0)} analyzed comments.
        """)
        
        # Key themes
        if topic_list:
            st.markdown("**🎯 Key Themes:**")
            theme_cols = st.columns(min(3, len(topic_list)))
            for i, topic in enumerate(topic_list[:6]):
                with theme_cols[i % 3]:
                    sentiment_emoji = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}.get(
                        topic.get("sentiment", "neutral"), "⚪")
                    st.info(f"{sentiment_emoji} **{topic.get('label', f'Theme {i+1}')}**\n\n"
                           f"_{topic.get('description', '')[:50]}..._\n\n"
                           f"� {topic.get('size', 0)} comments")
    
    # Card 2: What They Loved
    with report_tabs[1]:
        st.markdown("#### ❤️ What They Loved")
        if praises:
            for praise in praises[:5]:
                with st.container():
                    st.success(f"✓ {praise}")
        else:
            st.info("No major praises identified in the comments.")
    
    # Card 3: What Needs Attention  
    with report_tabs[2]:
        st.markdown("#### ⚠️ What Needs Attention")
        if criticisms:
            for criticism in criticisms[:5]:
                with st.container():
                    st.error(f"! {criticism}")
        else:
            st.success("✅ No major criticisms found! 🎉")
    
    # Card 4: Top Questions
    with report_tabs[3]:
        st.markdown("#### ❓ Top Viewer Questions")
        if questions:
            for i, question in enumerate(questions[:5], 1):
                with st.container():
                    st.warning(f"{i}. {question}")
            st.caption("💡 Consider addressing these in future content!")
        else:
            st.info("No specific questions found.")
    
    # Card 5: Smart Recommendations
    with report_tabs[4]:
        st.markdown("#### 💡 Smart Recommendations")
        
        recs = []
        if overall == "positive":
            recs.append("🎯 **Continue this format** - Your audience is responding well!")
        elif overall == "negative":
            recs.append("⚠️ **Address concerns** - Consider responding to feedback")
        
        if vibe >= 7:
            recs.append("🔥 **High engagement!** - Great time for community posts")
        elif vibe <= 4:
            recs.append("💡 **Boost interaction** - Add polls or questions")
        
        if praises and any("quality" in p.lower() or "production" in p.lower() for p in praises):
            recs.append("🎬 **Production value appreciated** - Continue investing in quality")
        
        if criticisms and any("length" in c.lower() or "long" in c.lower() for c in criticisms):
            recs.append("⏱️ **Consider shorter format** - Some viewers mention duration")
        
        if questions:
            recs.append(f"❓ **FAQ opportunity** - {len(questions)} questions could become content")
        
        for rec in recs:
            st.info(rec)
        
        if not recs:
            st.caption("Run more analyses to generate personalized recommendations")
    
    # Card 6: Vibe Check
    with report_tabs[5]:
        st.markdown("#### 🔥 Vibe Check")
        
        # Visual vibe indicator
        col_vibe, col_split = st.columns(2)
        
        with col_vibe:
            if vibe >= 8:
                st.balloons()
                st.success("## 🎉 Electric!\nYour community is HYPED!")
            elif vibe >= 6:
                st.success("## 😊 Positive Vibe\nGreat energy!")
            elif vibe >= 4:
                st.warning("## 😐 Neutral\nRoom for excitement")
            else:
                st.error("## 😔 Low Energy\nBoost engagement")
        
        with col_split:
            if sentiment_dist:
                st.markdown("**Sentiment Split**")
                st.metric("😊 Positive", f"{sentiment_dist.get('positive', 0)}%")
                st.metric("😔 Negative", f"{sentiment_dist.get('negative', 0)}%")
                st.metric("😐 Neutral", f"{sentiment_dist.get('neutral', 0)}%")
    
    # Raw report expander
    with st.expander("📄 View Original Text Report", expanded=False):
        st.markdown(report)

    st.success("✅ Analysis complete! Head to **AI Chat** to dive deeper into your audience insights.")
