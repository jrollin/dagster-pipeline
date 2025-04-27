# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DAGSTER_HOME=/opt/dagster/dagster_home

# Install system dependencies required for mariadb/mysql client and building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    mariadb-client \
    libmariadb-dev \
    default-mysql-client \
    awscli \
    # build-essential is needed for some package installations
    build-essential \
    # Clean up apt caches
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /opt/dagster/app

# Copy the requirements file first for cache optimization
COPY requirements.txt .

# Install Python dependencies
# Upgrade pip first
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create DAGSTER_HOME
RUN mkdir -p $DAGSTER_HOME

# Expose the port Dagster services run on (used by gRPC server)
EXPOSE 4000

# Command to run the Dagster code location server
# This makes the code available to the webserver and daemon
CMD ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "4000", "-f", "test_dagster/definitions.py"]
