from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

sys.path.insert(0, '/home/charu09/india-tech-pulse')

from scripts.fetch_hn import (
    fetch_top_stories,
    fetch_india_hn_stories,
    add_sentiment,
    save_results
)
from scripts.send_weekly_digest import send_digest

default_args = {
    'owner': 'charu',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

with DAG(
    dag_id='india_tech_pulse',
    default_args=default_args,
    description='Fetch HN India stories, analyze sentiment, save to S3 and RDS',
    schedule_interval='0 9 * * *',
    start_date=datetime(2026, 5, 1),
    catchup=False,
    tags=['india-tech-pulse'],
) as dag:

    def task_fetch_stories(**context):
        story_ids = fetch_top_stories(limit=200)
        stories = fetch_india_hn_stories(story_ids)
        context['ti'].xcom_push(key='stories', value=stories)

    def task_sentiment(**context):
        import pandas as pd
        stories = context['ti'].xcom_pull(key='stories', task_ids='fetch_stories')
        if not stories:
            raise ValueError("No stories found")
        df = pd.DataFrame(stories)
        df = add_sentiment(df)
        context['ti'].xcom_push(key='df_json', value=df.to_json())

    def task_save(**context):
        import pandas as pd
        import io
        df_json = context['ti'].xcom_pull(key='df_json', task_ids='run_sentiment')
        df = pd.read_json(io.StringIO(df_json))
        save_results(df)

    fetch_stories = PythonOperator(
        task_id='fetch_stories',
        python_callable=task_fetch_stories,
    )

    run_sentiment = PythonOperator(
        task_id='run_sentiment',
        python_callable=task_sentiment,
    )

    save_data = PythonOperator(
        task_id='save_data',
        python_callable=task_save,
    )

    weekly_digest = PythonOperator(
        task_id='send_weekly_digest',
        python_callable=send_digest,
        trigger_rule='all_done',
    )

    fetch_stories >> run_sentiment >> save_data >> weekly_digest
