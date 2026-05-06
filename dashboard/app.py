import streamlit as st
import pandas as pd
import boto3
import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

AWS_BUCKET = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")

st.set_page_config(
    page_title="India Tech Pulse",
    page_icon="🇮🇳",
    layout="wide"
)

@st.cache_data(ttl=3600)
def load_all_data():
    s3 = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    response = s3.list_objects_v2(Bucket=AWS_BUCKET, Prefix="daily/")
    files = [obj["Key"] for obj in response.get("Contents", [])]
    all_dfs = []
    for file in sorted(files):
        obj = s3.get_object(Bucket=AWS_BUCKET, Key=file)
        data = json.loads(obj["Body"].read())
        df = pd.DataFrame(data)
        all_dfs.append(df)
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame()

st.title("🇮🇳 India Tech Pulse")
st.caption("Daily sentiment tracking of Indian tech news — updated every morning automatically")

with st.spinner("Loading data from S3..."):
    df = load_all_data()

if df.empty:
    st.error("No data found. Run the pipeline first.")
    st.stop()

df["publishedAt"] = pd.to_datetime(df["publishedAt"], errors="coerce")
df["date"] = pd.to_datetime(df["date"], errors="coerce")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Articles", len(df))
col2.metric("Unique Sources", df["source"].nunique())
col3.metric("Positive", len(df[df["sentiment_label"] == "positive"]))
col4.metric("Negative", len(df[df["sentiment_label"] == "negative"]))

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Sentiment Breakdown")
    sentiment_counts = df["sentiment_label"].value_counts()
    st.bar_chart(sentiment_counts)

with col_right:
    st.subheader("📰 Top Sources")
    source_counts = df["source"].value_counts().head(8)
    st.bar_chart(source_counts)

st.divider()

col_pos, col_neg = st.columns(2)

with col_pos:
    st.subheader("🟢 Most Positive Headlines")
    top_pos = df.nlargest(5, "sentiment_score")[["title", "source", "sentiment_score"]]
    for _, row in top_pos.iterrows():
        st.markdown(f"**+{row['sentiment_score']:.2f}** · {row['source']}")
        st.markdown(f"_{row['title']}_")
        st.markdown("---")

with col_neg:
    st.subheader("🔴 Most Negative Headlines")
    top_neg = df.nsmallest(5, "sentiment_score")[["title", "source", "sentiment_score"]]
    for _, row in top_neg.iterrows():
        st.markdown(f"**{row['sentiment_score']:.2f}** · {row['source']}")
        st.markdown(f"_{row['title']}_")
        st.markdown("---")

st.divider()

st.subheader("🔍 Browse All Headlines")
sentiment_filter = st.selectbox("Filter by sentiment", ["All", "positive", "neutral", "negative"])
if sentiment_filter != "All":
    filtered = df[df["sentiment_label"] == sentiment_filter]
else:
    filtered = df
st.dataframe(
    filtered[["title", "source", "sentiment_label", "sentiment_score", "date"]].sort_values("sentiment_score"),
    use_container_width=True
)
