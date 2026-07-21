FROM python:3.12-slim

WORKDIR /app

# Install system dependencies required for building some python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download Presidio models during build so they don't download at runtime
RUN python -m spacy download en_core_web_lg

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
