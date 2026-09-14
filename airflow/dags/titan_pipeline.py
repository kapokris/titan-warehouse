from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/Users/rahulkapoor/Desktop/titan-warehouse"
PYTHON = f"{PROJECT_DIR}/venv/bin/python3"

with DAG(
    dag_id="titan_warehouse_pipeline",
    description="Generate, clean, and load Titan Warehouse data",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["titan"],
) as dag:

    generate_data = BashOperator(
        task_id="generate_data",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} scripts/01_generate_data.py",
    )

    transform_data = BashOperator(
        task_id="transform_data",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} scripts/02_transform.py",
    )

    load_warehouse = BashOperator(
        task_id="load_warehouse",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} scripts/03_load_warehouse.py",
    )

    generate_data >> transform_data >> load_warehouse