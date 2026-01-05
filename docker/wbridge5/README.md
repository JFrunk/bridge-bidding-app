# WBridge5 Oracle Service

This directory contains the Docker setup for running WBridge5 as a reference
bidding engine (oracle) for QA testing.

## Overview

WBridge5 is a world-class Windows bridge program that provides high-quality
SAYC bidding. We use it as a reference standard for validating our V2 Schema
engine. WBridge5 has won the World Computer Bridge Championship multiple times
(2005, 2007, 2008, 2016-2018).

## Quick Start

### 1. Download WBridge5

**Option A: Official Site**
1. Visit http://wbridge5.com/
2. Download the Windows installer
3. Extract `WBridge5.exe`

**Option B: Software Informer Mirror**
1. Visit https://wbridge5.software.informer.com/download/
2. Download and extract

### 2. Place the Binary

Copy `WBridge5.exe` to this directory:

```
docker/wbridge5/
├── Dockerfile
├── entrypoint.sh
├── wrapper_service.py
├── WBridge5.exe          # <-- Place here
└── README.md
```

### 3. Build the Docker Image

```bash
# From project root
docker build -t wbridge5-oracle ./docker/wbridge5
```

### 4. Run the Container

```bash
docker run -d -p 5005:5005 --name wbridge5-oracle wbridge5-oracle
```

### 5. Test the API

```bash
# Health check
curl http://localhost:5005/health

# Get bid recommendation
curl -X POST http://localhost:5005/bid \
  -H "Content-Type: application/json" \
  -d '{"hand": "KJ76.AQ84.5.J874", "history": ["1D"], "dealer": "N"}'
```

## API Endpoints

### GET /health
Health check endpoint.

Response:
```json
{
  "status": "healthy",
  "service": "wbridge5-qa",
  "mode": "live"
}
```

### GET /info
Service information.

### POST /bid
Get single bid recommendation.

Request:
```json
{
  "hand": "K92.QJT7.KQ4.AJ7",
  "history": ["1D", "Pass"],
  "vulnerability": "None",
  "dealer": "N"
}
```

Response:
```json
{
  "bid": "1NT",
  "explanation": "WBridge5 recommendation",
  "source": "wbridge5",
  "elapsed_ms": 150
}
```

### POST /batch
Process multiple hands.

Request:
```json
{
  "hands": [
    {"hand": "K92.QJT7.KQ4.AJ7", "history": ["1D", "Pass"]},
    {"hand": "AQ4.KJ5.T93.AKJ2", "history": []}
  ],
  "vulnerability": "None",
  "dealer": "N"
}
```

## Hand Notation

Hands are specified in S.H.D.C (Spades.Hearts.Diamonds.Clubs) notation:
- `K92.QJT7.KQ4.AJ7` = ♠K92 ♥QJ107 ♦KQ4 ♣AJ7
- `.AKQJ2.AKQ.KQJ2` = void in spades
- `T` represents 10

## Bid History Notation

Standard bridge notation:
- `1D`, `2H`, `3NT` = Level + Strain
- `Pass` or `P` = Pass
- `X` = Double
- `XX` = Redouble

## Integration with CI

The GitHub Actions workflow `v2_schema_baseline.yml` can optionally use WBridge5 as a reference:

```yaml
- name: Start WBridge5 Container
  run: |
    docker run -d -p 8081:8081 wbridge5-qa
    sleep 10  # Wait for container to start

- name: Run Tests with WBridge5 Reference
  run: |
    cd backend
    python3 tests/sayc_baseline/test_baseline_v2.py --wbridge5-url http://localhost:8081
```

## Limitations

1. **Wine Compatibility**: WBridge5 runs via Wine which may have compatibility issues
2. **Performance**: Wine adds overhead; batch processing is recommended
3. **Headless Mode**: Uses Xvfb for display; some GUI features unavailable
4. **License**: Ensure you have appropriate license for WBridge5 usage

## Troubleshooting

### Container won't start
```bash
docker logs wbridge5-qa
```

### WBridge5 not responding
Check Wine initialization:
```bash
docker exec -it wbridge5-qa bash
wine --version
ls -la ~/.wine/drive_c/WBridge5/
```

### Permission issues
Ensure WBridge5 files are owned by the wineuser:
```bash
docker exec -it wbridge5-qa ls -la /home/wineuser/.wine/drive_c/WBridge5/
```
