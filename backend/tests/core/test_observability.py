"""
Observability Tests
===================
"""
import pytest
from app.services.observability.metrics import (
    HTTP_REQUESTS_TOTAL,
    DB_CONNECTIONS,
    ML_TRAINING_JOBS_TOTAL,
    RAG_DOCUMENTS_INDEXED_TOTAL
)
from app.services.observability.alerts import AlertManager, AlertHandler

class TestObservabilityMetrics:
    def test_counter_increment(self):
        # Initial value or increment
        HTTP_REQUESTS_TOTAL.labels(method="GET", endpoint="/api/v1/health", status_code="200").inc()
        assert HTTP_REQUESTS_TOTAL.labels(method="GET", endpoint="/api/v1/health", status_code="200")._value.get() >= 1

    def test_gauge_set(self):
        DB_CONNECTIONS.set(5)
        assert DB_CONNECTIONS._value.get() == 5

    def test_ml_and_rag_metrics(self):
        ML_TRAINING_JOBS_TOTAL.labels(status="completed").inc()
        RAG_DOCUMENTS_INDEXED_TOTAL.inc(10)
        
        assert ML_TRAINING_JOBS_TOTAL.labels(status="completed")._value.get() >= 1
        assert RAG_DOCUMENTS_INDEXED_TOTAL._value.get() >= 10


class MockAlertHandler(AlertHandler):
    def __init__(self):
        self.alerts_sent = []
        
    def send(self, level: str, title: str, message: str, context: dict = None):
        self.alerts_sent.append({"level": level, "title": title, "message": message})


class TestAlertManager:
    def test_alert_routing(self):
        mock_handler = MockAlertHandler()
        AlertManager.register_handler(mock_handler)
        
        AlertManager.alert(
            level="CRITICAL",
            title="Database Offline",
            message="The primary database is unreachable."
        )
        
        assert len(mock_handler.alerts_sent) == 1
        assert mock_handler.alerts_sent[0]["level"] == "CRITICAL"
        assert mock_handler.alerts_sent[0]["title"] == "Database Offline"
