# IN India Tech Pulse

> Automated daily sentiment tracking of Indian tech news — updated every morning at 8am IST, zero manual work.

## 🔴 Live Dashboard
**[india-tech-pulse-jbshrzxp6f35vl6vvywitv.streamlit.app](https://india-tech-pulse-jbshrzxp6f35vl6vvywitv.streamlit.app)**

## What it does
Fetches 80–100 Indian tech headlines daily across 5 categories (startups, AI, layoffs, unicorns, technology), scores each headline's sentiment using VADER NLP, stores results in AWS S3, and serves live trend analysis on a public dashboard — fully automated via GitHub Actions.

## Architecture
NewsAPI → Python + pandas → VADER Sentiment → AWS S3 → Streamlit Dashboard
↑
GitHub Actions (daily 8am IST)

## Tech Stack
- **Data:** Python, pandas, NewsAPI
- **Sentiment:** VADER (vaderSentiment)
- **Cloud:** AWS S3, boto3
- **Automation:** GitHub Actions
- **Dashboard:** Streamlit (publicly deployed)
- **Containerization:** Docker (coming soon)

## Project Structure
india-tech-pulse/
├── scripts/
│   └── fetch_news.py      # main pipeline
├── dashboard/
│   └── app.py             # Streamlit dashboard
├── data/                  # local CSV/JSON output
├── .github/workflows/
│   └── daily_fetch.yml    # automation schedule
└── requirements.txt

## Features
- Fetches 80–100 articles daily across 5 targeted queries
- Removes duplicates and junk articles automatically
- Scores every headline: positive / negative / neutral
- Stores date-stamped JSON files in AWS S3 daily
- Dashboard shows sentiment breakdown, top sources, most positive/negative headlines
- Fully automated — runs itself every morning

## Setup
```bash
git clone https://github.com/drishikaa09/india-tech-pulse
cd india-tech-pulse
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Add your keys to `.env`:
NEWS_API_KEY=your_key
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_key
AWS_BUCKET_NAME=your_bucket
AWS_REGION=your_region

Then run:
```bash
python3 scripts/fetch_news.py
```

## Author
Drishika Tiwari — [github.com/drishikaa09](https://github.com/drishikaa09)
