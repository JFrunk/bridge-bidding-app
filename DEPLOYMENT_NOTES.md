# Deployment Notes

## AI Difficulty Configuration

The application now supports environment-based configuration for the default AI difficulty level.

### Development Setup (Current)

For local development on macOS (especially M1/M2 chips), the default is set to **intermediate** for stability:

```bash
# No environment variable needed - defaults to intermediate
python server.py
```

### Production Deployment (Recommended)

For production deployment, set the environment variable to enable **expert** mode by default:

```bash
# Set environment variable
export DEFAULT_AI_DIFFICULTY=expert

# Start server
python server.py
```

Or in your hosting platform (Render, Heroku, etc.):
1. Go to environment variables settings
2. Add: `DEFAULT_AI_DIFFICULTY` = `expert`
3. Restart the application

### Available Difficulty Levels

- `beginner` - 6/10 rating - Basic rule-based play
- `intermediate` - 7.5/10 rating - Enhanced evaluation with strategic thinking (default for dev)
- `advanced` - 8/10 rating - Deep analysis with tactical awareness
- `expert` - 9/10 rating - Double Dummy Solver for near-perfect play (recommended for production)

### Benefits of This Approach

1. **Development Stability**: Your local Mac development environment runs stable intermediate AI
2. **Production Excellence**: Production users get the best AI experience (expert mode)
3. **User Control**: Users can still change difficulty through the UI anytime
4. **Automatic Fallback**: If DDS isn't available, expert mode automatically falls back to deep Minimax AI (8+/10)

### Implementation Details

- Backend: [backend/core/session_state.py](backend/core/session_state.py#L35-38)
- Frontend automatically fetches the current default from backend
- Changes take effect on server restart
- No code changes needed between dev and production - just environment variables!
