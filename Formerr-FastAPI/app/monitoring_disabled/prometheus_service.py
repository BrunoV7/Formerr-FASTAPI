# app/monitoring/prometheus_service.py - METRICS BEAST MODE
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from fastapi import FastAPI
from typing import Dict, Any
import time
import psutil
import os


class PrometheusMetrics:
    """Beast Mode Prometheus Metrics for Formerr"""

    def __init__(self):
        # 🔥 CUSTOM METRICS PARA FORMERR

        # Counters - Eventos que só crescem
        self.forms_created_total = Counter(
            'formerr_forms_created_total',
            'Total number of forms created',
            ['user_role', 'form_type']
        )

        self.submissions_total = Counter(
            'formerr_submissions_total',
            'Total number of form submissions',
            ['form_id', 'form_title', 'success']
        )

        self.emails_sent_total = Counter(
            'formerr_emails_sent_total',
            'Total emails sent',
            ['email_type', 'status']  # email_type: invitation|auth_code|notification
        )

        self.webhooks_triggered_total = Counter(
            'formerr_webhooks_triggered_total',
            'Total webhooks triggered',
            ['event_type', 'status', 'response_code']
        )

        self.auth_attempts_total = Counter(
            'formerr_auth_attempts_total',
            'Authentication attempts',
            ['method', 'status']  # method: github|jwt, status: success|failure
        )

        # Histograms - Distribuição de tempos
        self.request_duration = Histogram(
            'formerr_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint', 'status_code']
        )

        self.database_query_duration = Histogram(
            'formerr_database_query_duration_seconds',
            'Database query duration',
            ['table', 'operation']  # operation: select|insert|update|delete
        )

        self.webhook_response_time = Histogram(
            'formerr_webhook_response_time_seconds',
            'Webhook response time',
            ['webhook_url', 'event_type']
        )

        self.email_send_duration = Histogram(
            'formerr_email_send_duration_seconds',
            'Email sending duration',
            ['email_type', 'provider']
        )

        # Gauges - Valores que sobem e descem
        self.active_forms = Gauge(
            'formerr_active_forms_count',
            'Number of active forms',
            ['user_role']
        )

        self.concurrent_users = Gauge(
            'formerr_concurrent_users',
            'Number of concurrent authenticated users'
        )

        self.database_connections = Gauge(
            'formerr_database_connections_active',
            'Active database connections'
        )

        self.memory_usage_bytes = Gauge(
            'formerr_memory_usage_bytes',
            'Memory usage in bytes'
        )

        self.cpu_usage_percent = Gauge(
            'formerr_cpu_usage_percent',
            'CPU usage percentage'
        )

        # Info - Metadata
        self.app_info = Info(
            'formerr_app_info',
            'Formerr application information'
        )

        # Set app info
        self.app_info.info({
            'version': '1.0.0-brunov7-beast-mode',
            'developer': 'BrunoV7',
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'deployment_date': '2025-06-18T03:54:25Z',
            'git_commit': 'beast-mode-prometheus',
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
        })

    def track_form_created(self, user_role: str, form_type: str = "standard"):
        """Track form creation"""
        self.forms_created_total.labels(
            user_role=user_role,
            form_type=form_type
        ).inc()

    def track_submission(self, form_id: str, form_title: str, success: bool):
        """Track form submission"""
        self.submissions_total.labels(
            form_id=form_id,
            form_title=form_title[:50],  # Limit length
            success=str(success).lower()
        ).inc()

    def track_email_sent(self, email_type: str, status: str):
        """Track email sending"""
        self.emails_sent_total.labels(
            email_type=email_type,
            status=status
        ).inc()

    def track_webhook_triggered(self, event_type: str, status: str, response_code: int):
        """Track webhook trigger"""
        self.webhooks_triggered_total.labels(
            event_type=event_type,
            status=status,
            response_code=str(response_code)
        ).inc()

    def track_auth_attempt(self, method: str, success: bool):
        """Track authentication attempt"""
        self.auth_attempts_total.labels(
            method=method,
            status="success" if success else "failure"
        ).inc()

    def observe_database_query(self, table: str, operation: str, duration: float):
        """Observe database query duration"""
        self.database_query_duration.labels(
            table=table,
            operation=operation
        ).observe(duration)

    def observe_webhook_response_time(self, webhook_url: str, event_type: str, duration: float):
        """Observe webhook response time"""
        # Simplify URL for metrics (remove query params, etc)
        simple_url = webhook_url.split('?')[0].split('#')[0]
        if len(simple_url) > 100:
            simple_url = simple_url[:100] + "..."

        self.webhook_response_time.labels(
            webhook_url=simple_url,
            event_type=event_type
        ).observe(duration)

    def observe_email_duration(self, email_type: str, provider: str, duration: float):
        """Observe email sending duration"""
        self.email_send_duration.labels(
            email_type=email_type,
            provider=provider
        ).observe(duration)

    def update_active_forms_count(self, user_role: str, count: int):
        """Update active forms gauge"""
        self.active_forms.labels(user_role=user_role).set(count)

    def update_concurrent_users(self, count: int):
        """Update concurrent users gauge"""
        self.concurrent_users.set(count)

    def update_database_connections(self, count: int):
        """Update database connections gauge"""
        self.database_connections.set(count)

    def update_system_metrics(self):
        """Update system resource metrics"""
        # Memory usage
        memory = psutil.virtual_memory()
        self.memory_usage_bytes.set(memory.used)

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_usage_percent.set(cpu_percent)


# Global instance
prometheus_metrics = PrometheusMetrics()