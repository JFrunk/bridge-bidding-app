"""
Routes module for Flask API endpoints

Contains modular route registration functions that can be imported and
registered with the Flask app.
"""

from .room_api import register_room_endpoints

__all__ = ['register_room_endpoints']
