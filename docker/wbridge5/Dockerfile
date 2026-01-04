# WBridge5 Docker Container for Bridge Bidding QA
#
# This container runs WBridge5 (Windows bridge program) via Wine
# to provide reference bidding decisions for our test suite.
#
# Build:
#   docker build -t wbridge5-qa ./docker/wbridge5
#
# Run:
#   docker run -p 8081:8081 wbridge5-qa
#
# API Endpoints:
#   POST /bid - Get bid recommendation from WBridge5
#   POST /batch - Process multiple hands
#   GET /health - Health check

FROM ubuntu:22.04

# Avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV WINEDEBUG=-all

# Install Wine and dependencies
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        wine32 \
        wine64 \
        winetricks \
        xvfb \
        python3 \
        python3-pip \
        wget \
        unzip \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create wine user (Wine doesn't like running as root)
RUN useradd -m -s /bin/bash wineuser
USER wineuser
WORKDIR /home/wineuser

# Initialize Wine prefix
RUN wineboot --init && \
    winetricks -q vcrun2019 corefonts

# Download and install WBridge5
# Note: WBridge5 is available from http://wbridge5.com/
# The actual download URL may need to be updated
RUN mkdir -p /home/wineuser/.wine/drive_c/WBridge5

# Copy WBridge5 application (must be provided during build)
# Users should download WBridge5 and place in the build context
COPY --chown=wineuser:wineuser wbridge5/ /home/wineuser/.wine/drive_c/WBridge5/

# Install Python requirements for the wrapper service
USER root
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Copy the wrapper service
COPY --chown=wineuser:wineuser wbridge5_service.py /app/wbridge5_service.py

USER wineuser
WORKDIR /app

# Expose the API port
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Start the service with Xvfb for headless operation
CMD ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1024x768x24", \
     "python3", "wbridge5_service.py"]
