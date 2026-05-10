import boto3
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def get_weekly_stories():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode="require"
    )
    cur = conn.cursor()
    one_week_ago = datetime.now() - timedelta(days=7)
    cur.execute("""
        SELECT title, url, score, by, fetched_at
        FROM hn_stories
        WHERE fetched_at >= %s
        ORDER BY score DESC
        LIMIT 10
    """, (one_week_ago,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def build_html(stories):
    today = datetime.now().strftime("%B %d, %Y")
    rows_html = ""
    for i, (title, url, score, by, fetched_at) in enumerate(stories, 1):
        link = f'<a href="{url}">{title}</a>' if url else title
        rows_html += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #eee;">{i}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;">{link}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;">{score}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;">{by}</td>
        </tr>"""

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;padding:20px;">
        <h2 style="color:#ff6600;">🇮🇳 India Tech Pulse — Weekly Digest</h2>
        <p style="color:#666;">Week ending {today}</p>
        <p>Here are the top India-relevant stories from Hacker News this week:</p>
        <table style="width:100%;border-collapse:collapse;">
            <tr style="background:#f5f5f5;">
                <th style="padding:8px;text-align:left;">#</th>
                <th style="padding:8px;text-align:left;">Story</th>
                <th style="padding:8px;text-align:left;">Score</th>
                <th style="padding:8px;text-align:left;">Author</th>
            </tr>
            {rows_html}
        </table>
        <p style="color:#999;font-size:12px;margin-top:30px;">
            Powered by India Tech Pulse — AWS S3 + RDS + Airflow pipeline
        </p>
    </body>
    </html>
    """

def send_digest():
    stories = get_weekly_stories()
    if not stories:
        print("No stories this week, skipping digest.")
        return

    html = build_html(stories)
    ses = boto3.client(
        "ses",
        region_name=os.getenv("AWS_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    ses.send_email(
        Source="0903charutiwari@gmail.com",
        Destination={"ToAddresses": ["0903charutiwari@gmail.com"]},
        Message={
            "Subject": {"Data": f"🇮🇳 India Tech Pulse — Weekly Digest {datetime.now().strftime('%b %d')}"},
            "Body": {"Html": {"Data": html}}
        }
    )
    print(f"✅ Digest sent! {len(stories)} stories included.")

if __name__ == "__main__":
    send_digest()
