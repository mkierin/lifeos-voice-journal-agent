FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download FastEmbed model to make startup faster and more reliable
RUN python -c "from qdrant_client import QdrantClient; client = QdrantClient(':memory:'); client.add('temp', documents=['init'], ids=[1])"

COPY bot/ ./bot/

CMD ["python", "-m", "bot.main"]
