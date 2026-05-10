import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

st.set_page_config(
    page_title="India Tech Pulse",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.main {
    background-color: #0a0a0f;
}

[data-testid="stSidebar"] {
    background-color: #0f0f18;
    border-right: 1px solid #1e1e2e;
}

.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 3.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ff6b35 0%, #f7931e 50%, #ffcd3c 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
    margin-bottom: 0.3rem;
}

.hero-subtitle {
    font-family: 'DM Sans', sans-serif;
    font-size: 1.05rem;
    color: #6b7280;
    font-weight: 300;
    letter-spacing: 0.02em;
}

.metric-card {
    background: linear-gradient(135deg, #12121e 0%, #1a1a2e 100%);
    border: 1px solid #2a2a3e;
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, #ff6b35, #f7931e, #ffcd3c);
}

.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: #f0f0f0;
    line-height: 1;
    margin-bottom: 0.3rem;
}

.metric-label {
    font-size: 0.78rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 500;
}

.story-card {
    background: #12121e;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.7rem;
    transition: border-color 0.2s;
    position: relative;
}

.story-card:hover {
    border-color: #ff6b35;
}

.story-rank {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    color: #ff6b35;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    font-weight: 600;
    margin-bottom: 0.4rem;
}

.story-title {
    font-size: 1rem;
    color: #e8e8f0;
    font-weight: 500;
    line-height: 1.4;
    margin-bottom: 0.5rem;
}

.story-meta {
    font-size: 0.8rem;
    color: #4b5563;
    display: flex;
    gap: 1rem;
}

.sentiment-positive { color: #10b981; }
.sentiment-negative { color: #ef4444; }
.sentiment-neutral { color: #6b7280; }

.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #e8e8f0;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1e1e2e;
}

.tag {
    display: inline-block;
    background: #1e1e2e;
    color: #9ca3af;
    font-size: 0.72rem;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    margin-right: 0.3rem;
    font-weight: 500;
}

.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
    font-size: 0.72rem;
    padding: 0.25rem 0.8rem;
    border-radius: 20px;
    border: 1px solid rgba(16, 185, 129, 0.2);
    font-weight: 500;
    letter-spacing: 0.05em;
}

.footer-text {
    font-size: 0.75rem;
    color: #374151;
    text-align: center;
    padding-top: 2rem;
    letter-spacing: 0.05em;
}

div[data-testid="stExpander"] {
    background: #12121e !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 12px !important;
}

.stSelectbox > div, .stSlider > div {
    color: #e8e8f0;
}
</style>
""", unsafe_allow_html=True)

PLOT_LAYOUT = dict(
    plot_bgcolor="#0a0a0f",
    paper_bgcolor="#0a0a0f",
    font=dict(color="#9ca3af", family="DM Sans"),
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(gridcolor="#1e1e2e", showline=False, zeroline=False),
    yaxis=dict(gridcolor="#1e1e2e", showline=False, zeroline=False),
    showlegend=False,
)

@st.cache_data(ttl=300)
def load_data(days=30):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            sslmode="require"
        )
        since = datetime.now() - timedelta(days=days)
        df = pd.read_sql("""
            SELECT story_id, title, url, score, by, descendants, fetched_at
            FROM hn_stories
            WHERE fetched_at >= %s
            ORDER BY score DESC
        """, conn, params=(since,))
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return pd.DataFrame()

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 0 2rem;">
        <div style="font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 800;
                    background: linear-gradient(135deg, #ff6b35, #ffcd3c);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    background-clip: text;">
            India Tech Pulse
        </div>
        <div style="font-size: 0.75rem; color: #4b5563; margin-top: 0.2rem;">
            HN Intelligence Dashboard
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Filters")
    days = st.slider("Time range (days)", 1, 90, 30)
    min_score = st.slider("Min score", 0, 500, 0)

    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.75rem; color: #374151; line-height: 1.8;">
        <div>🏗 AWS S3 + RDS</div>
        <div>⚡ Apache Airflow</div>
        <div>🔧 Terraform IaC</div>
        <div>📬 AWS SES Digest</div>
    </div>
    """, unsafe_allow_html=True)

# Main content
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.markdown('<div class="hero-title">India Tech Pulse</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Real-time tracker of India\'s presence on Hacker News</div>', unsafe_allow_html=True)
with col_badge:
    st.markdown('<br><br><span class="live-badge">● LIVE</span>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

df = load_data(days)

if df.empty:
    st.warning("No stories found. Run `python3 scripts/fetch_hn.py` to populate the database.")
    st.stop()

df_f = df[df["score"] >= min_score].copy()
df_f["fetched_at"] = pd.to_datetime(df_f["fetched_at"])
df_f["date"] = df_f["fetched_at"].dt.date

if df_f.empty:
    st.warning("No stories match your filters.")
    st.stop()

# Metrics
c1, c2, c3, c4 = st.columns(4)
metrics = [
    (len(df_f), "Stories tracked"),
    (f"{df_f['score'].mean():.0f}", "Avg HN score"),
    (df_f['score'].max(), "Top score"),
    (df_f['by'].nunique(), "Unique authors"),
]
for col, (val, label) in zip([c1, c2, c3, c4], metrics):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{val}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Charts
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown('<div class="section-header">Stories over time</div>', unsafe_allow_html=True)
    daily = df_f.groupby("date").agg(count=("story_id", "count"), avg_score=("score", "mean")).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily["date"], y=daily["count"],
        marker_color="#ff6b35",
        marker_line_width=0,
        hovertemplate="<b>%{x}</b><br>Stories: %{y}<extra></extra>"
    ))
    fig.update_layout(**PLOT_LAYOUT, height=240)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown('<div class="section-header">Score distribution</div>', unsafe_allow_html=True)
    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(
        x=df_f["score"],
        nbinsx=15,
        marker_color="#f7931e",
        marker_line_width=0,
        hovertemplate="Score range: %{x}<br>Count: %{y}<extra></extra>"
    ))
    fig2.update_layout(**PLOT_LAYOUT, height=240)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Top stories
st.markdown('<div class="section-header">Top stories</div>', unsafe_allow_html=True)

top_stories = df_f.nlargest(10, "score")
for i, (_, row) in enumerate(top_stories.iterrows(), 1):
    title_html = f'<a href="{row["url"]}" target="_blank" style="color:#e8e8f0; text-decoration:none;">{row["title"]}</a>' if row.get("url") else row["title"]
    st.markdown(f"""
    <div class="story-card">
        <div class="story-rank">#{i} &nbsp;·&nbsp; {str(row["fetched_at"])[:10]}</div>
        <div class="story-title">{title_html}</div>
        <div class="story-meta">
            <span>⬆ {int(row['score'])} points</span>
            <span>💬 {int(row['descendants']) if row.get('descendants') else 0} comments</span>
            <span>👤 {row['by']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Author leaderboard
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-header">Top authors</div>', unsafe_allow_html=True)
    top_authors = df_f.groupby("by")["score"].sum().nlargest(8).reset_index()
    fig3 = px.bar(top_authors, x="score", y="by", orientation="h",
                  color_discrete_sequence=["#ffcd3c"])
    fig3.update_layout(
        plot_bgcolor="#0a0a0f",
        paper_bgcolor="#0a0a0f",
        font=dict(color="#9ca3af", family="DM Sans"),
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(gridcolor="#1e1e2e", showline=False, zeroline=False),
        yaxis=dict(gridcolor="#1e1e2e", showline=False, zeroline=False, tickfont=dict(size=11)),
        showlegend=False,
        height=280
    )
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    st.markdown('<div class="section-header">Recent activity</div>', unsafe_allow_html=True)
    recent = df_f.sort_values("fetched_at", ascending=False).head(6)
    for _, row in recent.iterrows():
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center;
                    padding: 0.6rem 0; border-bottom: 1px solid #1e1e2e;">
            <span style="font-size:0.85rem; color:#d1d5db; flex:1; margin-right:1rem;
                         white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                {row['title'][:55]}{'...' if len(row['title']) > 55 else ''}
            </span>
            <span style="font-size:0.8rem; color:#ff6b35; font-weight:600; white-space:nowrap;">
                ⬆ {int(row['score'])}
            </span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<div class="footer-text">
    INDIA TECH PULSE &nbsp;·&nbsp; AWS S3 + RDS + AIRFLOW + TERRAFORM &nbsp;·&nbsp; BUILT BY CHARU TIWARI
</div>
""", unsafe_allow_html=True)
