# CORS AI Play Fix - November 26, 2025

## Issue

**Error:** `Access to fetch at 'https://bridge-bidding-api.onrender.com/api/get-ai-play' from origin 'https://bridge-bidding-app.onrender.com' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`

**Symptom:** AI not playing cards on production (Render). The AI loop would pause ("AI: ⏸") and the game would be stuck waiting for AI to play.

**Environment:** Production (Render)

## Root Cause

The Flask-CORS configuration was using the simple `CORS(app)` setup which works for successful responses but doesn't guarantee CORS headers on error responses.

When an error occurred in the `/api/get-ai-play` endpoint (e.g., "No play in progress" due to session state loss on Render), the error response was missing CORS headers, causing the browser to block the response entirely.

The browser's preflight (OPTIONS) request also needed proper handling.

## Solution

Enhanced the CORS configuration in `backend/server.py`:

### 1. Explicit CORS Configuration

```python
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-Session-ID", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": False
    }
})
```

### 2. Global Error Handlers

Added error handlers that ensure CORS headers are included even on errors:

```python
@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all exceptions and ensure CORS headers are included."""
    response = jsonify({"error": str(e), "type": type(e).__name__})
    response.status_code = 500
    return response

@app.errorhandler(400)
def handle_bad_request(e):
    """Handle 400 errors with CORS headers."""
    response = jsonify({"error": str(e.description) if hasattr(e, 'description') else str(e)})
    response.status_code = 400
    return response

@app.errorhandler(404)
def handle_not_found(e):
    response = jsonify({"error": "Not found"})
    response.status_code = 404
    return response

@app.errorhandler(500)
def handle_internal_error(e):
    response = jsonify({"error": "Internal server error"})
    response.status_code = 500
    return response
```

## Verification

After the fix, error responses now include proper CORS headers:

```
HTTP/1.1 400 BAD REQUEST
Access-Control-Allow-Origin: https://bridge-bidding-app.onrender.com
Access-Control-Expose-Headers: Content-Type
...
{"error": "No play in progress"}
```

## Files Changed

- `backend/server.py` - Enhanced CORS configuration and added global error handlers

## Testing

1. Start backend locally
2. Test preflight request:
   ```bash
   curl -I -X OPTIONS http://localhost:5001/api/get-ai-play \
     -H "Origin: https://bridge-bidding-app.onrender.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type, X-Session-ID"
   ```
3. Verify `Access-Control-Allow-Origin` header is present
4. Test error response:
   ```bash
   curl -i -X POST http://localhost:5001/api/get-ai-play \
     -H "Origin: https://bridge-bidding-app.onrender.com" \
     -H "Content-Type: application/json" \
     -H "X-Session-ID: test-no-session" \
     -d '{}'
   ```
5. Verify CORS headers are present even on 400 error response

## Related

- Session state loss on Render: `docs/domains/learning/bug-fixes/AI_REVIEW_SESSION_FIX_2025-11-26.md`
- Previous CORS issues: None documented (first occurrence)
