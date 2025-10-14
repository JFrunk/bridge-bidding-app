"""
Authentication module for Bridge Bidding App
MVP version: Email-only authentication, no passwords
"""

from .simple_auth_api import register_simple_auth_endpoints

__all__ = ['register_simple_auth_endpoints']
