import requests
import pandas as pd
import boto3
import json
import os
import logging
from dotenv import load_dotenv
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

load_dotenv()

AWS_BUCKET = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")
TODAY = datetime.now().strftime("%Y-%m-%d")

INDIA_KEYWORDS = [
    # Cities
    "india", "indian", "bangalore", "bengaluru", "mumbai",
    "delhi", "hyderabad", "pune", "chennai", "kolkata",
    "ahmedabad", "jaipur", "noida", "gurgaon", "gurugram",
    # Big tech companies
    "infosys", "wipro", "tata consultancy", "tcs",
    "hcl technologies", "tech mahindra", "cognizant india",
    # Conglomerates
    "reliance industries", "adani", "mahindra",
    # Unicorns & startups
    "zomato", "swiggy", "razorpay", "cred", "zepto",
    "flipkart", "paytm", "byju", "meesho",
    "naukri", "freshworks", "zoho", "inmobi", "unacademy",
    "phonepe", "groww", "upstox", "khatabook",
    "lenskart", "mamaearth", "dream11",
    "blinkit", "dunzo", "rapido", "sharechat", "dailyhunt",
    "ola electric", "ather energy",
    # Ecosystem & policy
    "iit", "iim", "iitb", "iitd", "iitm",
    "sequoia india", "accel india",
    "startup india", "digital india", "atmanirbhar",
    "upi", "npci", "aadhaar",
    "india stack", "bharat",
    # Finance
    "sensex", "nse india", "bse india",
    "sebi india", "rbi india",
    # Space & science
    "isro", "chandrayaan", "gaganyaan",
    # Telecom
    "jio", "airtel india",
    # Diaspora
    "indian diaspora", "indian american", "indian origin",
]

def fetch_top_stories(limit=500):
    logger.info("Fetching Hacker News top stories...")
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    response = requests.get(url, timeout=10)
    story_ids = response.json()[:limit]
    logger.info(f"Got {len(story_ids)} story IDs")
    return story_ids

def fetch_story(story_id):
    url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
    try:
        response = requests.get(url, timeout=5)
        return response.json()
    except:
        return None

EXCLUDE_TERMS = ["openindiana", "indiana", "india ink", "india rubber"]

def is_india_relevant(title):
    if not title:
        return False
    title_lower = title.lower()
    if any(excl in title_lower for excl in EXCLUDE_TERMS):
        return False
    return any(
        f" {keyword} " in f" {title_lower} " or
        title_lower.startswith(keyword) or
        title_lower.endswith(keyword)
        for keyword in INDIA_KEYWORDS
    )

def fetch_india_hn_stories(story_ids):
    india_stories = []
    checked = 0
    for story_id in story_ids:
        story = fetch_story(story_id)
        if not story:
            continue
        checked += 1
        title = story.get("title", "")
        if is_india_relevant(title):
            india_stories.append({
                "title": title,
                "url": story.get("url", ""),
                "score": story.get("score", 0),
                "comments": story.get("descendants", 0),
                "by": story.get("by", ""),
                "time": story.get("time", 0),
                "story_id": story_id,
                "source": "Hacker News"
            })
    logger.info(f"Checked {checked} stories, found {len(india_stories)} India-relevant")
    return india_stories

def add_sentiment(df):
    analyzer = SentimentIntensityAnalyzer()
    df["sentiment_score"] = df["title"].apply(
        lambda x: analyzer.polarity_scores(x)["compound"]
    )
    df["sentiment_label"] = df["sentiment_score"].apply(
        lambda x: "positive" if x >= 0.05 else ("negative" if x <= -0.05 else "neutral")
    )
    df["date"] = TODAY
    logger.info("Sentiment analysis complete")
    return df

def save_to_rds(df):
    try:
        from sqlalchemy import create_engine, text
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT", "5432")
        dbname = os.getenv("DB_NAME")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        engine = create_engine(
            f"postgresql+pg8000://{user}:{password}@{host}:{port}/{dbname}",
            connect_args={"ssl_context": True}
        )
        inserted = 0
        with engine.connect() as conn:
            for _, row in df.iterrows():
                result = conn.execute(text("""
                    INSERT INTO hn_stories (story_id, title, url, score, by, time, descendants)
                    VALUES (:story_id, :title, :url, :score, :by, :time, :descendants)
                    ON CONFLICT (story_id) DO NOTHING
                """), {
                    "story_id": row["story_id"],
                    "title": row["title"],
                    "url": row["url"],
                    "score": row["score"],
                    "by": row["by"],
                    "time": row["time"],
                    "descendants": row["comments"]
                })
                inserted += result.rowcount
            conn.commit()
        logger.info(f"Saved {inserted} new stories to RDS")
    except Exception as e:
        logger.error(f"RDS insert failed: {e}")

def save_results(df):
    os.makedirs("data", exist_ok=True)

    csv_path = f"data/{TODAY}_hn.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved CSV → {csv_path}")

    json_path = f"data/{TODAY}_hn.json"
    df.to_json(json_path, orient="records", indent=2, date_format="iso")
    logger.info(f"Saved JSON → {json_path}")

    try:
        s3 = boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        s3_key = f"hn/{TODAY}_hn.json"
        s3.upload_file(json_path, AWS_BUCKET, s3_key)
        logger.info(f"Uploaded to S3 → s3://{AWS_BUCKET}/{s3_key}")
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
    save_to_rds(df)

def print_summary(df):
    print("\n" + "="*60)
    print(f"  HACKER NEWS INDIA — {TODAY}")
    print("="*60)
    print(f"  Stories found    : {len(df)}")
    print(f"  Avg HN score     : {df['score'].mean():.1f}")
    print(f"  Avg comments     : {df['comments'].mean():.1f}")
    print("="*60)

    print("\n── Sentiment Breakdown ───────────────────────────────────")
    print(df["sentiment_label"].value_counts().to_string())

    print("\n── Most Upvoted Stories ──────────────────────────────────")
    top = df.nlargest(5, "score")[["title", "score", "comments", "sentiment_score"]]
    for _, row in top.iterrows():
        print(f"\n  Score: {int(row['score'])} points | {int(row['comments'])} comments | sentiment: {row['sentiment_score']:+.2f}")
        print(f"  {row['title']}")

    print("\n── Most Discussed ────────────────────────────────────────")
    discussed = df.nlargest(3, "comments")[["title", "comments"]]
    for _, row in discussed.iterrows():
        print(f"\n  {int(row['comments'])} comments")
        print(f"  {row['title']}")

    print("\n" + "="*60)

if __name__ == "__main__":
    logger.info("Starting Hacker News India fetch...")
    story_ids = fetch_top_stories(limit=200)
    stories = fetch_india_hn_stories(story_ids)

    if not stories:
        logger.warning("No India-relevant stories found today on HN front page.")
        logger.info("This is normal — try increasing limit or check back tomorrow.")
    else:
        df = pd.DataFrame(stories)
        df = add_sentiment(df)
        save_results(df)
        print_summary(df)

    logger.info("Done. ✓")
