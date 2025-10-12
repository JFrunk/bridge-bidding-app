"""
DEPRECATED: This file is kept for backward compatibility only.

Please use: from engine.play.ai.simple_ai import SimplePlayAI

This file will be removed in a future version.
"""

import warnings
from engine.play.ai.simple_ai import SimplePlayAI as _SimplePlayAI

# Show deprecation warning
warnings.warn(
    "Importing from engine.simple_play_ai is deprecated. "
    "Use 'from engine.play.ai.simple_ai import SimplePlayAI' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backward compatibility
SimplePlayAI = _SimplePlayAI

__all__ = ['SimplePlayAI']
