import requests
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
# ── Load env ───────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")

if not API_KEY:
    raise ValueError("NEWS_API_KEY not found in .env file. Please add it.")

# ── Constants ──────────────────────────────────────────────────
QUERIES = [
    "Indian startup",
    "India technology",
    "Indian tech layoffs",
    "India AI",
    "Indian unicorn"
]
TODAY = datetime.now().strftime("%Y-%m-%d")

# ── Fetch ──────────────────────────────────────────────────────
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

# ── Clean ──────────────────────────────────────────────────────
def clean_articles(articles):
    if not articles:
        logger.warning("No articles to clean.")
        return pd.DataFrame()

    df = pd.DataFrame(articles)

    # Keep only useful columns
    df = df[["title", "description", "source", "publishedAt", "url", "search_query"]]

    # Flatten source dict → source name string
    df["source"] = df["source"].apply(lambda x: x["name"] if isinstance(x, dict) else x)

    # Parse datetime and extract date
    df["publishedAt"] = pd.to_datetime(df["publishedAt"], utc=True, errors="coerce")
    df["date"] = df["publishedAt"].dt.strftime("%Y-%m-%d")

    # Drop rows with no title or description
    df = df.dropna(subset=["title", "description"])

    # Remove duplicates by title
    before = len(df)
    df = df.drop_duplicates(subset=["title"])
    after = len(df)
    logger.info(f"Removed {before - after} duplicate articles")

    # Remove articles with removed/deleted content
    df = df[~df["title"].str.contains(r"\[Removed\]", na=False)]
    df = df[~df["description"].str.contains(r"\[Removed\]", na=False)]

    # Reset index cleanly
    df = df.reset_index(drop=True)

    return df

# ── Save ───────────────────────────────────────────────────────
def save_results(df):
    os.makedirs("data", exist_ok=True)

    # Save CSV
    csv_path = f"data/{TODAY}_news.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved CSV → {csv_path}")

    # Save JSON (useful for S3 later)
    json_path = f"data/{TODAY}_news.json"
    df.to_json(json_path, orient="records", indent=2, date_format="iso")
    logger.info(f"Saved JSON → {json_path}")

# ── Summary ────────────────────────────────────────────────────
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

    print("\n── Latest Headlines ──────────────────────────────────────")
    latest = df[["title", "source", "date"]].head(10)
    for _, row in latest.iterrows():
        print(f"\n  [{row['source']}] {row['date']}")
        print(f"  {row['title']}")
    print("\n" + "="*60)

# ── Main ───────────────────────────────────────────────────────
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
