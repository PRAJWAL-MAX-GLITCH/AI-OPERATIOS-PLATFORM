"""
Alert Framework
===============
Alerting abstraction for critical system events in the Enterprise AI Operations Platform.
"""
import structlog
from typing import Dict, Any, List

logger = structlog.get_logger(__name__)

class AlertHandler:
    """Base interface for all alert handlers."""
    def send(self, level: str, title: str, message: str, context: Dict[str, Any] = None):
        raise NotImplementedError()

class EmailAlertHandler(AlertHandler):
    def send(self, level: str, title: str, message: str, context: Dict[str, Any] = None):
        logger.info("alert_sent_email", level=level, title=title)

class SlackAlertHandler(AlertHandler):
    def send(self, level: str, title: str, message: str, context: Dict[str, Any] = None):
        logger.info("alert_sent_slack", level=level, title=title)

class WebhookAlertHandler(AlertHandler):
    def send(self, level: str, title: str, message: str, context: Dict[str, Any] = None):
        logger.info("alert_sent_webhook", level=level, title=title)

class AlertManager:
    """Manages routing of alerts to registered handlers."""
    
    _handlers: List[AlertHandler] = [
        EmailAlertHandler(),
        SlackAlertHandler(),
        WebhookAlertHandler()
    ]

    @classmethod
    def register_handler(cls, handler: AlertHandler):
        cls._handlers.append(handler)

    @classmethod
    def alert(cls, level: str, title: str, message: str, context: Dict[str, Any] = None):
        """Dispatch an alert to all registered handlers."""
        logger.error("system_alert", level=level, title=title, message=message, context=context)
        for handler in cls._handlers:
            try:
                handler.send(level, title, message, context)
            except Exception as e:
                logger.error("alert_handler_failed", handler=type(handler).__name__, error=str(e))
