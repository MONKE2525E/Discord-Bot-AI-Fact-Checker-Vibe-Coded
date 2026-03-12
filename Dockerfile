FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Whisper and yt-dlp
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create temp directory for downloads
RUN mkdir -p temp_downloads

# Expose port for webhook (optional)
EXPOSE 8080

# Run the bot
CMD ["python", "tiktok_factcheck.py"]
