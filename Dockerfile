# FairLens AI — Dockerfile
# Optimized for Google Cloud Run deployment (port 8080)

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (leverages Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Cloud Run requires the container to listen on port 8080
EXPOSE 8080

# Start the FastAPI app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
