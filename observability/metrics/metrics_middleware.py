"""
Prometheus metrics middleware for Flask/FastAPI applications.

Provides automatic instrumentation of HTTP requests with:
- Request counters
- Request duration histograms
- Exception counters
"""

import time
from collections.abc import Callable
from functools import wraps

from flask import Flask, Response, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

# Define Prometheus metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

http_requests_exceptions_total = Counter(
    "http_requests_exceptions_total",
    "Total HTTP requests that raised exceptions",
    ["method", "endpoint", "exception_type"],
)


class MetricsMiddleware:
    """
    Flask middleware for automatic Prometheus metrics collection.

    Usage:
        from observability.metrics.metrics_middleware import MetricsMiddleware

        app = Flask(__name__)
        MetricsMiddleware(app)
    """

    def __init__(self, app: Flask | None = None):
        """
        Initialize the metrics middleware.

        Args:
            app: Flask application instance
        """
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """
        Initialize the middleware with a Flask app.

        Args:
            app: Flask application instance
        """

        # Register metrics endpoint
        @app.route("/metrics")
        def metrics():
            """Prometheus metrics endpoint"""
            return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

        # Register before/after request handlers
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)

        # Store app reference
        self.app = app

    def _before_request(self):
        """Record request start time"""
        request._start_time = time.time()

    def _after_request(self, response: Response) -> Response:
        """Record metrics after successful request"""
        if hasattr(request, "_start_time"):
            # Calculate request duration
            duration = time.time() - request._start_time

            # Get endpoint (use path as fallback)
            endpoint = request.endpoint or request.path

            # Record metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method, endpoint=endpoint
            ).observe(duration)

        return response

    def _teardown_request(self, exception=None):
        """Record exception metrics if request failed"""
        if exception is not None:
            endpoint = request.endpoint or request.path
            exception_type = type(exception).__name__

            http_requests_exceptions_total.labels(
                method=request.method, endpoint=endpoint, exception_type=exception_type
            ).inc()


def track_function_metrics(metric_name: str):
    """
    Decorator to track custom function execution metrics.

    Usage:
        @track_function_metrics("process_payment")
        def process_payment():
            # business logic
            pass

    Args:
        metric_name: Name for the metric
    """
    # Define custom metrics for this function
    function_calls_total = Counter(
        f"{metric_name}_calls_total", f"Total calls to {metric_name}", ["status"]
    )

    function_duration_seconds = Histogram(
        f"{metric_name}_duration_seconds",
        f"Execution time for {metric_name} in seconds",
        buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                function_calls_total.labels(status=status).inc()
                function_duration_seconds.observe(duration)

        return wrapper

    return decorator


# Convenience export
metrics_client = {
    "requests_total": http_requests_total,
    "request_duration": http_request_duration_seconds,
    "exceptions_total": http_requests_exceptions_total,
}
