"""
OpenTelemetry tracer configuration and utilities.

Provides automatic instrumentation and manual span creation for distributed tracing.
"""

import os

from flask import Flask
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# Global tracer provider
_tracer_provider: TracerProvider | None = None
_is_initialized = False


def init_tracing(app: Flask | None = None, service_name: str = "magsasa-card-erp", service_version: str = "1.0.0", otlp_endpoint: str | None = None, console_export: bool = True, _):
    """
    Initialize OpenTelemetry tracing for the application.

    Args:
        app: Flask application to instrument (optional)
        service_name: Name of the service for tracing
        service_version: Version of the service
        otlp_endpoint: OTLP collector endpoint (e.g., "http://localhost:4317")
        console_export: Whether to export traces to console (for debugging)

    Usage:
        from observability.tracing.otel_tracer import init_tracing

        app = Flask(__name__)
        init_tracing(app)
    """
    global _tracer_provider, _is_initialized

    if _is_initialized:
        return

    # Read configuration from environment variables
    otlp_endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    service_name = os.getenv("OTEL_SERVICE_NAME", service_name)

    # Create resource with service information
    resource = Resource(
        attributes={
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        }
    )

    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)

    # Add span processors
    if otlp_endpoint:
        # Export to OTLP collector (e.g., Jaeger, Tempo)
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    if console_export:
        # Export to console for debugging
        console_exporter = ConsoleSpanExporter()
        _tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Set as global tracer provider
    trace.set_tracer_provider(_tracer_provider)

    # Auto-instrument Flask app
    if app is not None:
        FlaskInstrumentor().instrument_app(app)

    # Auto-instrument requests library
    RequestsInstrumentor().instrument()

    # Auto-instrument SQLAlchemy (if using it)
    try:
        SQLAlchemyInstrumentor().instrument()
    except Exception:
        pass  # SQLAlchemy might not be available

    _is_initialized = True


def get_tracer(name: str = __name__) -> trace.Tracer:
    """
    Get a tracer instance for creating spans.

    Args:
        name: Name of the tracer (typically __name__)

    Returns:
        Tracer instance

    Usage:
        from observability.tracing.otel_tracer import get_tracer

        tracer = get_tracer(__name__)

        with tracer.start_as_current_span("process_data"):
            # business logic here
            pass
    """
    if not _is_initialized:
        # Initialize with defaults if not already done
        init_tracing()

    return trace.get_tracer(name)


def add_span_attributes(_**attributes):
    """
    Add attributes to the current span.

    Args:
        **attributes: Key-value pairs to add as span attributes

    Usage:
        from observability.tracing.otel_tracer import add_span_attributes

        add_span_attributes(user_id="123", transaction_id="txn_456")
    """
    span = trace.get_current_span()
    if span.is_recording():
        for _key, value in attributes.items():
            span.set_attribute(key, value)


def add_span_event(_name: str, attributes: dict | None = None):
    """
    Add an event to the current span.

    Args:
        name: Name of the event
        attributes: Optional attributes for the event

    Usage:
        from observability.tracing.otel_tracer import add_span_event

        add_span_event("payment_initiated", {"amount": 1000, "currency": "PHP"})
    """
    span = trace.get_current_span()
    if span.is_recording():
        span.add_event(name, attributes=attributes or {})


def get_trace_context(_):
    """
    Get the current trace context (trace_id, span_id).

    Returns:
        Dictionary with trace_id and span_id (or None if not in a span)

    Usage:
        from observability.tracing.otel_tracer import get_trace_context

        context = get_trace_context()
        print(f"Trace ID: {context['trace_id']}, Span ID: {context['span_id']}")
    """
    span = trace.get_current_span()
    if span.is_recording():
        span_context = span.get_span_context()
        return {
            "trace_id": format(span_context.trace_id, "032x"),
            "span_id": format(span_context.span_id, "016x"),
        }
    return {"trace_id": None, "span_id": None}
