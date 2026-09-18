FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for psycopg2 and other native modules
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose the API port
EXPOSE 8001

# Command to run the application
CMD ["python", "api_server.py"]
