# MariaDB to S3 Dagster Pipeline (with Local Dependencies)

This project contains a Dagster pipeline designed to extract data from a specified MariaDB table and upload it to an S3-compatible store (AWS S3 or local MinIO) in Parquet format. The setup uses Docker Compose to run Dagster services along with local versions of MariaDB (for source data) and MinIO (for S3-compatible storage).

## Prerequisites

*   Docker ([Install Docker](https://docs.docker.com/get-docker/))
*   Docker Compose ([Install Docker Compose](https://docs.docker.com/compose/install/))

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd test-dagster
    ```

2.  **Configure environment variables:**
    Copy `.env.example` to `.env`:
    ```bash
    cp .env.example .env
    ```
    **Edit the `.env` file:**
    *   **Source MariaDB:** By default, it's configured to connect to the `source-mariadb` container running within Docker Compose. You **MUST** set the `MARIADB_TABLE` variable to the name of the table you want to extract from this database.
        ```dotenv
        MARIADB_TABLE=your_source_table # <<< CHANGE THIS!
        ```
        You can optionally change `SOURCE_DB_USER`, `SOURCE_DB_PASSWORD`, `SOURCE_DB_NAME` if needed (defaults are `sourceuser`, `sourcepassword`, `sourcedb`).
    *   **Target S3/MinIO:** By default, it's configured to use the local `minio` container. The `MINIO_ENDPOINT_URL` directs the pipeline to use it. The `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set to MinIO's default credentials (`minioadmin`). You should set the `S3_BUCKET` name (e.g., `local-dagster-bucket`); the `create-minio-bucket` service will attempt to create this bucket in MinIO on startup.
        ```dotenv
        S3_BUCKET=local-dagster-bucket # Or your desired bucket name
        ```
    *   **Connecting to External Services:** If you want to connect to an *external* MariaDB source or *actual* AWS S3, comment out the local configuration lines in `.env` (like `MARIADB_HOST=source-mariadb` and `MINIO_ENDPOINT_URL`) and uncomment/configure the sections for external connections, providing your real credentials and endpoints.
    *   **Internal Dagster DB:** You generally don't need to change the `DAGSTER_DB_*` variables unless you want to customize the internal database credentials.

3.  **(Optional) Initialize Source Database:**
    *   Create a SQL script (e.g., `init-source-db.sql`) in the project root directory.
    *   In this script, create the table specified in `MARIADB_TABLE` and insert some sample data.
    *   Uncomment the volume mount line in the `source-mariadb` service definition in `docker-compose.yml`:
        ```yaml
        volumes:
          - ./init-source-db.sql:/docker-entrypoint-initdb.d/init.sql # < UNCOMMENT THIS
          - source_mariadb_data:/var/lib/mysql
        ```
    This script will run automatically when the `source-mariadb` container starts for the first time.

## Running the Pipeline with Docker Compose

1.  **Build and start the services:**
    Run the following command from the project's root directory:
    ```bash
    docker-compose up --build -d
    ```
    This command will:
    *   Build the Docker image for your Dagster code (`dagster-user-code`).
    *   Start all services: `dagster-mariadb` (internal), `source-mariadb`, `minio`, `create-minio-bucket`, `dagster-user-code`, `dagster-webserver`, and `dagster-daemon` in detached mode (`-d`).

2.  **Access the Dagster UI (Dagit):**
    Open your web browser and navigate to `http://localhost:3000`.
    You should see the `mariadb_s3_code_location` and the assets/jobs defined within it.

3.  **Access MinIO Console:**
    Open `http://localhost:9001` in your browser. Log in using the `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` from your `.env` file (defaults are `minioadmin`/`minioadmin`). You can view the created bucket and uploaded Parquet files here.

4.  **Triggering Runs:**
    *   **Manually:** You can materialize assets (`mariadb_table_extract`, `upload_to_s3`) or launch the `mariadb_to_s3_job` directly from the UI.
    *   **Scheduled:** The `nightly_schedule` is configured to run the `mariadb_to_s3_job` automatically every night at midnight UTC. You can view and manage schedules in the UI under the "Schedules" tab.

## Stopping the Services

To stop the running Docker containers:

```bash
docker-compose down
```

To stop and remove the volumes (including MariaDB data and MinIO data):

```bash
docker-compose down -v
```

## Development

*   If you make changes to the Python code in `test_dagster/`, you need to rebuild the `dagster-user-code` image:
    ```bash
    docker-compose build dagster-user-code
    docker-compose up -d --no-deps dagster-user-code # Restart only the user code service
    ```
    Then, reload the workspace in the Dagster UI.
*   Check container logs:
    ```bash
    docker-compose logs -f <service_name> # e.g., dagster-webserver, dagster-user-code, minio, source-mariadb
    ```
