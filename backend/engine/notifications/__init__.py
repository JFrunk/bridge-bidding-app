"""Notification services for Bridge Bidding App."""

from .email_service import EmailService, get_email_service, send_review_notification

__all__ = ['EmailService', 'get_email_service', 'send_review_notification']
