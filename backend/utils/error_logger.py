"""
Structured Error Logging System

Provides comprehensive error tracking with:
- Structured logging (JSON format)
- Context capture (request, user, session)
- Error categorization
- Automatic aggregation
- Pattern detection
"""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib

# Configure logging directory
LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Error log files
ERROR_LOG_FILE = LOG_DIR / 'errors.jsonl'
ERROR_SUMMARY_FILE = LOG_DIR / 'error_summary.json'


class ErrorLogger:
    """Structured error logger with automatic categorization and aggregation"""

    def __init__(self):
        self.logger = self._setup_logger()
        self.error_counts = self._load_error_summary()

    def _setup_logger(self):
        """Configure structured JSON logger"""
        logger = logging.getLogger('bridge_error_logger')
        logger.setLevel(logging.ERROR)

        # JSON file handler
        handler = logging.FileHandler(ERROR_LOG_FILE)
        handler.setLevel(logging.ERROR)
        logger.addHandler(handler)

        return logger

    def _load_error_summary(self) -> Dict[str, Any]:
        """Load error summary from disk"""
        if ERROR_SUMMARY_FILE.exists():
            with open(ERROR_SUMMARY_FILE, 'r') as f:
                return json.load(f)
        return {
            'total_errors': 0,
            'by_category': {},
            'by_endpoint': {},
            'by_error_hash': {},
            'first_seen': {},
            'last_seen': {},
            'occurrences': {}
        }

    def _save_error_summary(self):
        """Persist error summary to disk"""
        with open(ERROR_SUMMARY_FILE, 'w') as f:
            json.dump(self.error_counts, f, indent=2)

    def _categorize_error(self, error: Exception, context: Dict[str, Any]) -> str:
        """Categorize error type"""
        error_type = type(error).__name__

        # AI/Bidding errors
        if 'bidding' in str(error).lower() or 'convention' in str(error).lower():
            return 'bidding_logic'

        # Play engine errors
        if 'play' in str(error).lower() or 'trick' in str(error).lower():
            return 'play_engine'

        # Database errors
        if 'database' in str(error).lower() or 'sqlite' in str(error).lower():
            return 'database'

        # API/Request errors
        if context.get('endpoint'):
            return 'api'

        # Performance errors
        if 'timeout' in str(error).lower() or 'performance' in str(error).lower():
            return 'performance'

        # Default
        return error_type

    def _generate_error_hash(self, error: Exception, context: Dict[str, Any]) -> str:
        """Generate unique hash for error pattern"""
        # Use error type + message + stack trace location
        error_signature = f"{type(error).__name__}:{str(error)}"

        # Add stack trace top frame
        tb = traceback.extract_tb(error.__traceback__)
        if tb:
            top_frame = tb[-1]
            error_signature += f":{top_frame.filename}:{top_frame.lineno}"

        return hashlib.md5(error_signature.encode()).hexdigest()[:12]

    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None
    ):
        """
        Log error with full context

        Args:
            error: Exception that occurred
            context: Additional context (auction state, hand data, etc.)
            user_id: User who encountered error
            endpoint: API endpoint where error occurred
            request_data: Request payload
        """
        context = context or {}

        # Generate error record
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'category': self._categorize_error(error, context),
            'user_id': user_id,
            'endpoint': endpoint,
            'traceback': traceback.format_exc(),
            'context': context,
            'request_data': request_data
        }

        # Generate error hash for pattern detection
        error_hash = self._generate_error_hash(error, context)
        error_record['error_hash'] = error_hash

        # Log to file (JSONL format - one JSON object per line)
        with open(ERROR_LOG_FILE, 'a') as f:
            f.write(json.dumps(error_record) + '\n')

        # Update error summary
        self._update_summary(error_record)

        # Console output for immediate visibility
        print(f"🚨 ERROR LOGGED: [{error_record['category']}] {error_record['error_type']}: {error_record['error_message']}")
        print(f"   Hash: {error_hash} | Endpoint: {endpoint} | User: {user_id}")

    def _update_summary(self, error_record: Dict[str, Any]):
        """Update error aggregation summary"""
        category = error_record['category']
        endpoint = error_record['endpoint'] or 'unknown'
        error_hash = error_record['error_hash']
        timestamp = error_record['timestamp']

        # Total count
        self.error_counts['total_errors'] += 1

        # By category
        self.error_counts['by_category'][category] = \
            self.error_counts['by_category'].get(category, 0) + 1

        # By endpoint
        self.error_counts['by_endpoint'][endpoint] = \
            self.error_counts['by_endpoint'].get(endpoint, 0) + 1

        # By error hash (pattern detection)
        self.error_counts['by_error_hash'][error_hash] = \
            self.error_counts['by_error_hash'].get(error_hash, 0) + 1

        # First/last seen
        if error_hash not in self.error_counts['first_seen']:
            self.error_counts['first_seen'][error_hash] = timestamp
        self.error_counts['last_seen'][error_hash] = timestamp

        # Occurrence count
        self.error_counts['occurrences'][error_hash] = \
            self.error_counts['occurrences'].get(error_hash, 0) + 1

        # Persist summary
        self._save_error_summary()

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics"""
        return self.error_counts

    def get_top_errors(self, limit: int = 10) -> list:
        """Get most frequent errors"""
        sorted_errors = sorted(
            self.error_counts['by_error_hash'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_errors[:limit]

    def get_recent_errors(self, limit: int = 50) -> list:
        """Get most recent errors from log file"""
        if not ERROR_LOG_FILE.exists():
            return []

        with open(ERROR_LOG_FILE, 'r') as f:
            lines = f.readlines()

        # Parse last N lines
        recent = []
        for line in lines[-limit:]:
            try:
                recent.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        return list(reversed(recent))  # Most recent first

    def detect_patterns(self) -> Dict[str, Any]:
        """Detect recurring error patterns"""
        patterns = {
            'high_frequency_errors': [],  # Errors occurring >10 times
            'recent_spikes': [],          # Errors with sudden increase
            'critical_endpoints': [],     # Endpoints with >5 errors
            'affected_users': []          # Users encountering multiple errors
        }

        # High frequency errors
        for error_hash, count in self.error_counts['by_error_hash'].items():
            if count > 10:
                patterns['high_frequency_errors'].append({
                    'hash': error_hash,
                    'count': count,
                    'first_seen': self.error_counts['first_seen'].get(error_hash),
                    'last_seen': self.error_counts['last_seen'].get(error_hash)
                })

        # Critical endpoints
        for endpoint, count in self.error_counts['by_endpoint'].items():
            if count > 5:
                patterns['critical_endpoints'].append({
                    'endpoint': endpoint,
                    'error_count': count
                })

        return patterns


# Global error logger instance
error_logger = ErrorLogger()


def log_error(error: Exception, **kwargs):
    """Convenience function for logging errors"""
    error_logger.log_error(error, **kwargs)


def get_error_summary():
    """Convenience function for getting error summary"""
    return error_logger.get_error_summary()


def get_recent_errors(limit: int = 50):
    """Convenience function for getting recent errors"""
    return error_logger.get_recent_errors(limit)


def detect_error_patterns():
    """Convenience function for pattern detection"""
    return error_logger.detect_patterns()
