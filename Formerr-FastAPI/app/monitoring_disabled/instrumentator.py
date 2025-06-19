from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Response
from app.monitoring.prometheus_service import prometheus_metrics
import time


def setup_prometheus_instrumentator(app: FastAPI):
    """Setup Prometheus instrumentator for FastAPI"""

    # Create instrumentator
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=[".*admin.*", "/metrics"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="formerr_requests_inprogress",
        inprogress_labels=True,
    )

    # Add default metrics - CORRIGIDO
    instrumentator.add(
        metrics.request_size(
            should_include_handler=True,
            should_include_method=True,
            should_include_status=True,
            metric_namespace="formerr",
            metric_subsystem="http",
        )
    ).add(
        metrics.response_size(
            should_include_handler=True,
            should_include_method=True,
            should_include_status=True,
            metric_namespace="formerr",
            metric_subsystem="http",
        )
    ).add(
        metrics.latency(
            should_include_handler=True,
            should_include_method=True,
            should_include_status=True,
            metric_namespace="formerr",
            metric_subsystem="http",
        )
    ).add(
        metrics.requests(
            should_include_handler=True,
            should_include_method=True,
            should_include_status=True,
            metric_namespace="formerr",
            metric_subsystem="http",
        )
    )

    # Custom metric function - CORRIGIDO
    def brunov7_beast_mode_metric(info: metrics.Info) -> None:
        """Custom metric for BrunoV7 Beast Mode tracking"""
        if hasattr(info, 'modified_handler') and info.modified_handler:
            # Track API endpoint usage
            if "/api/forms" in info.modified_handler:
                prometheus_metrics.forms_created_total.labels(
                    user_role="unknown",
                    form_type="api_call"
                ).inc()

            elif "/api/public/forms" in info.modified_handler and hasattr(info, 'method') and info.method == "POST":
                prometheus_metrics.submissions_total.labels(
                    form_id="public_submission",
                    form_title="public_form",
                    success=str(info.response.status_code < 400).lower()
                ).inc()

    # Add custom metric - CORRIGIDO
    instrumentator.add(brunov7_beast_mode_metric)

    # Instrument the app
    instrumentator.instrument(app)

    # Add metrics endpoint
    @app.get("/metrics")
    async def metrics_endpoint():
        """Prometheus metrics endpoint"""
        # Update system metrics before serving
        prometheus_metrics.update_system_metrics()

        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )

    return instrumentator