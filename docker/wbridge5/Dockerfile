# WBridge5 Docker Container for Bridge Bidding QA
#
# This container runs WBridge5 (Windows bridge program) via Wine
# to provide reference bidding decisions for our test suite.
#
# Prerequisites:
#   1. Download WBridge5 from wbridge5.com
#   2. Place WBridge5.exe in this directory
#
# Build:
#   docker build -t wbridge5-oracle ./docker/wbridge5
#
# Run:
#   docker run -p 5005:5005 wbridge5-oracle
#
# API Endpoints:
#   POST /bid - Get bid recommendation from WBridge5
#   POST /batch - Process multiple hands
#   GET /health - Health check

FROM python:3.9-slim-bullseye

# 1. Enable 32-bit architecture (CRITICAL for WBridge5)
RUN dpkg --add-architecture i386

# 2. Avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# 3. Install Wine, Xvfb (Virtual Display), and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wine \
    wine32 \
    xvfb \
    curl \
    netcat-openbsd \
    procps \
    xdotool \
    x11-utils \
    && rm -rf /var/lib/apt/lists/*

# 4. Set up working directory
WORKDIR /app

# 5. Install Python dependencies
RUN pip install --no-cache-dir flask requests

# 6. Environment Variables for Wine
ENV WINEPREFIX=/root/.wine
ENV WINEARCH=win32
# Suppress Wine debug messages to keep logs clean
ENV WINEDEBUG=-all

# 7. Copy application files
# WBridge5.exe must be present in the build context
COPY WBridge5.exe /app/WBridge5.exe
COPY wrapper_service.py /app/wrapper_service.py
COPY entrypoint.sh /app/entrypoint.sh

# 8. Set permissions
RUN chmod +x /app/entrypoint.sh

# 9. Expose the API port
EXPOSE 5005

# 10. Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5005/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
