# 🇮🇳 India Tech Pulse

A fully automated data engineering pipeline that tracks India-relevant stories on Hacker News daily, performs sentiment analysis, and visualises results on a live dashboard.

## Live Dashboard
**[india-tech-pulse-jbshrzxp6f35vl6vvywitv.streamlit.app](https://india-tech-pulse.streamlit.app/)**

## How it works

1. GitHub Actions triggers the pipeline daily at 9am IST
2. Fetches top 200 HN stories and filters for India-relevant content
3. Runs VADER sentiment analysis on each headline
4. Stores results in AWS S3 (data lake) and PostgreSQL RDS (data warehouse)
5. Dashboard reads from RDS and displays live trends

## Tech Stack

- **Pipeline** — Python, Hacker News API, VADER NLP
- **Storage** — AWS S3, AWS RDS (PostgreSQL)
- **Orchestration** — GitHub Actions, Apache Airflow
- **Infrastructure** — Terraform, Docker, AWS ECS Fargate, AWS ECR
- **Notifications** — AWS SES weekly email digest
- **Dashboard** — Streamlit, Plotly

## Run locally

```bash
git clone https://github.com/drishikaa09/india-tech-pulse
cd india-tech-pulse
pip install -r requirements.txt
cp .env.example .env  # fill in your credentials
python3 scripts/fetch_hn.py
streamlit run app.py
```

## Author
Drishika Tiwari · [github.com/drishikaa09](https://github.com/drishikaa09)
