"""Dagster definitions for the MariaDB to S3 pipeline."""

import os
import mariadb
import pandas as pd
from dagster import Definitions, asset, EnvVar, Config, materialize, ScheduleDefinition, define_asset_job
from dagster_aws.s3 import S3Resource
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# --- Configuration Schemas ---

class MariaDBConfig(Config):
    """Configuration for connecting to MariaDB."""
    user: str = EnvVar("MARIADB_USER")
    password: str = EnvVar("MARIADB_PASSWORD")
    host: str = EnvVar("MARIADB_HOST")
    port: str = EnvVar("MARIADB_PORT")
    database: str = EnvVar("MARIADB_DATABASE")
    table: str = EnvVar("MARIADB_TABLE")

class S3UploadConfig(Config):
    """Configuration for uploading to S3."""
    s3_bucket: str = EnvVar("S3_BUCKET")
    s3_key_prefix: str = EnvVar("S3_KEY_PREFIX")

# --- Resources ---

# Define the S3 resource using dagster-aws
s3_resource = S3Resource(
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"), # Reads from MINIO_ROOT_USER in local setup
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"), # Reads from MINIO_ROOT_PASSWORD in local setup
    endpoint_url=os.getenv("MINIO_ENDPOINT_URL") # Optional: Use MINIO_ENDPOINT_URL if set
)

# --- Assets ---

@asset
def mariadb_table_extract(context, config: MariaDBConfig) -> pd.DataFrame:
    """Extracts data from the specified MariaDB table into a Pandas DataFrame."""
    try:
        conn = mariadb.connect(
            user=config.user,
            password=config.password,
            host=config.host,
            port=int(config.port),
            database=config.database
        )
        cursor = conn.cursor()
        query = f"SELECT * FROM {config.table}"
        context.log.info(f"Connecting to MariaDB: host={config.host}, port={config.port}, database={config.database}, table={config.table}")
        cursor.execute(query)
        # Fetch data into a Pandas DataFrame
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=[desc[0] for desc in cursor.description])
        cursor.close()
        conn.close()
        return df
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB or executing query: {e}")
        raise

@asset
def upload_to_s3(
    context,
    config: S3UploadConfig,
    s3: S3Resource,
    mariadb_table_extract: pd.DataFrame
) -> str:
    """Uploads the extracted DataFrame to S3 as a Parquet file."""
    df = mariadb_table_extract
    if df.empty:
        context.log.info("DataFrame is empty, skipping S3 upload.")
        return "No data to upload"

    # Generate a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{timestamp}.parquet"
    s3_key = os.path.join(config.s3_key_prefix, file_name)

    # Convert DataFrame to Parquet format in memory
    parquet_buffer = df.to_parquet(index=False)

    # Upload to S3
    s3_client = s3.get_client()
    s3_path = f"s3://{config.s3_bucket}/{s3_key}"
    context.log.info(f"Uploading Parquet data to {s3_path}...")
    try:
        s3_client.put_object(
            Bucket=config.s3_bucket,
            Key=s3_key,
            Body=parquet_buffer
        )
        context.log.info(f"Successfully uploaded data to {s3_path}")
        return s3_path
    except Exception as e:
        context.log.error(f"Failed to upload data to {s3_path}: {e}")
        raise

# --- Jobs ---

# Define a job that targets both assets
mariadb_to_s3_job = define_asset_job(
    name="mariadb_to_s3_job",
    selection=[mariadb_table_extract, upload_to_s3]
)

# --- Schedules ---

# Define a schedule to run the job nightly at midnight UTC
nightly_schedule = ScheduleDefinition(
    job=mariadb_to_s3_job,
    cron_schedule="0 0 * * *",  # Every day at midnight UTC
    execution_timezone="UTC",
)

# --- Definitions ---

defs = Definitions(
    assets=[mariadb_table_extract, upload_to_s3],
    resources={
        "s3": s3_resource,
    },
    jobs=[mariadb_to_s3_job],      # Add the job
    schedules=[nightly_schedule], # Add the schedule
)

# Example of how to materialize assets locally (for testing)
if __name__ == "__main__":
    # Ensure you have a .env file with credentials
    # or environment variables set before running this.
    print("Attempting to materialize assets locally...")
    print("Ensure .env file is present and populated, or environment variables are set.")
    result = materialize(
        assets=[mariadb_table_extract, upload_to_s3],
        resources={"s3": s3_resource}
    )
    print(f"Asset materialization result: {result.success}")
