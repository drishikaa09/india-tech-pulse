import requests
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime
import json
import logging
import boto3
from botocore.exceptions import ClientError
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")
AWS_BUCKET = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")
if not API_KEY:
    raise ValueError("NEWS_API_KEY not found in .env file. Please add it.")

QUERIES = [
    "Indian startup",
    "India technology",
    "Indian tech layoffs",
    "India AI",
    "Indian unicorn"
]
TODAY = datetime.now().strftime("%Y-%m-%d")

def fetch_tech_news():
    all_articles = []
    for query in QUERIES:
        logger.info(f"Fetching articles for: '{query}'")
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 20,
            "apiKey": API_KEY
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "ok":
                logger.warning(f"API returned non-ok status for '{query}': {data.get('message')}")
                continue
            articles = data.get("articles", [])
            for article in articles:
                article["search_query"] = query
            all_articles.extend(articles)
            logger.info(f"Got {len(articles)} articles for '{query}'")
        except requests.exceptions.Timeout:
            logger.error(f"Request timed out for query: '{query}'")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for '{query}': {e}")
    return all_articles

def clean_articles(articles):
    if not articles:
        logger.warning("No articles to clean.")
        return pd.DataFrame()
    df = pd.DataFrame(articles)
    df = df[["title", "description", "source", "publishedAt", "url", "search_query"]]
    df["source"] = df["source"].apply(lambda x: x["name"] if isinstance(x, dict) else x)
    df["publishedAt"] = pd.to_datetime(df["publishedAt"], utc=True, errors="coerce")
    df["date"] = df["publishedAt"].dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["title", "description"])
    before = len(df)
    df = df.drop_duplicates(subset=["title"])
    after = len(df)
    logger.info(f"Removed {before - after} duplicate articles")
    df = df[~df["title"].str.contains(r"\[Removed\]", na=False)]
    df = df[~df["description"].str.contains(r"\[Removed\]", na=False)]
    analyzer = SentimentIntensityAnalyzer()
    df["sentiment_score"] = df["title"].apply(
        lambda x: analyzer.polarity_scores(x)["compound"]
    )
    df["sentiment_label"] = df["sentiment_score"].apply(
        lambda x: "positive" if x >= 0.05 else ("negative" if x <= -0.05 else "neutral")
    )
    logger.info("Sentiment analysis complete")
    df = df.reset_index(drop=True)
    return df

def save_results(df):
    os.makedirs("data", exist_ok=True)
    csv_path = f"data/{TODAY}_news.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved CSV → {csv_path}")
    json_path = f"data/{TODAY}_news.json"
    df.to_json(json_path, orient="records", indent=2, date_format="iso")
    logger.info(f"Saved JSON → {json_path}")
# ── Upload to S3 ───────────────────────────────────────────
    try:
        s3 = boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        s3_key = f"daily/{TODAY}_news.json"
        s3.upload_file(json_path, AWS_BUCKET, s3_key)
        logger.info(f"Uploaded to S3 → s3://{AWS_BUCKET}/{s3_key}")
    except ClientError as e:
        logger.error(f"S3 upload failed: {e}")

def print_summary(df):
    print("\n" + "="*60)
    print(f"  INDIA TECH PULSE — {TODAY}")
    print("="*60)
    print(f"  Total articles fetched : {len(df)}")
    print(f"  Unique sources         : {df['source'].nunique()}")
    print(f"  Queries covered        : {df['search_query'].nunique()}")
    print("="*60)

    print("\n── Top Sources ───────────────────────────────────────────")
    print(df["source"].value_counts().head(5).to_string())

    print("\n── Articles by Query ─────────────────────────────────────")
    print(df["search_query"].value_counts().to_string())

    print("\n── Sentiment Breakdown ───────────────────────────────────")
    print(df["sentiment_label"].value_counts().to_string())

    print("\n── Most Positive Headlines ───────────────────────────────")
    top_positive = df.nlargest(3, "sentiment_score")[["title", "sentiment_score"]]
    for _, row in top_positive.iterrows():
        print(f"\n  Score: {row['sentiment_score']:+.2f}")
        print(f"  {row['title']}")

    print("\n── Most Negative Headlines ───────────────────────────────")
    top_negative = df.nsmallest(3, "sentiment_score")[["title", "sentiment_score"]]
    for _, row in top_negative.iterrows():
        print(f"\n  Score: {row['sentiment_score']:+.2f}")
        print(f"  {row['title']}")

    print("\n── Latest Headlines ──────────────────────────────────────")
    latest = df[["title", "source", "date"]].head(10)
    for _, row in latest.iterrows():
        print(f"\n  [{row['source']}] {row['date']}")
        print(f"  {row['title']}")

    print("\n" + "="*60)

if __name__ == "__main__":
    logger.info("Starting India Tech Pulse fetch...")
    articles = fetch_tech_news()
    df = clean_articles(articles)
    if df.empty:
        logger.error("No data to save. Check your API key or internet connection.")
    else:
        save_results(df)
        print_summary(df)
        logger.info("Done. ✓")

