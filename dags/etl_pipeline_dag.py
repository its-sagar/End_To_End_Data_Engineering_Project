from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime


# Import ETL functions
from extract.github_extractor import extract_github_data
from transform.bronze_to_silver import load_data_from_bronze
from transform.silver_to_gold.dim_branch import create_dim_branch
from transform.silver_to_gold.dim_dealer import create_dim_dealer
from transform.silver_to_gold.dim_model import create_dim_model
from transform.silver_to_gold.dim_date import create_dim_date
from transform.silver_to_gold.fact_sales import create_fact_sales


default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

with DAG(
    dag_id='etl_pipeline_dag',
    default_args=default_args,
    description='Full ETL pipeline from GitHub to fact table',
    schedule_interval=None,  # Trigger manually or via GitHub webhook
    catchup=False,
    tags=['etl', 'data_pipeline'],
) as dag:

    t1_ingest = PythonOperator(
        task_id='github_data_ingestion',
        python_callable=extract_github_data
    )

    t2_transform_bronze = PythonOperator(
        task_id='transform_bronze_to_silver',
        python_callable=load_data_from_bronze
    )

    t3_dim_branch = PythonOperator(
        task_id='load_dim_branch',
        python_callable=create_dim_branch
    )

    t4_dim_dealer = PythonOperator(
        task_id='load_dim_dealer',
        python_callable=create_dim_dealer
    )

    t5_dim_model = PythonOperator(
        task_id='load_dim_model',
        python_callable=create_dim_model
    )

    t6_dim_date = PythonOperator(
        task_id='load_dim_date',
        python_callable=create_dim_date
    )

    t7_fact_sales = PythonOperator(
        task_id='load_fact_sales',
        python_callable=create_fact_sales
    )

    # Define dependencies
    t1_ingest >> t2_transform_bronze >> [t3_dim_branch, t4_dim_dealer, t5_dim_model, t6_dim_date] >> t7_fact_sales
