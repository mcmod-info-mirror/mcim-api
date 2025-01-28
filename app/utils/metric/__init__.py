from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_client import Gauge, CollectorRegistry, Counter
from fastapi import FastAPI

APP_REGISTRY = CollectorRegistry()


FILE_CDN_FORWARD_TO_ORIGIN_COUNT = Counter(
    "origin_forwarded_total",
    "Number of times has been forwarded to origin.",
    labelnames=("platform",),
    registry=APP_REGISTRY,
)

FILE_CDN_FORWARD_TO_OPEN93HOME_COUNT = Counter(
    "open93home_forwarded_total",
    "Number of times has been forwarded to open93home.",
    labelnames=("platform",),
    registry=APP_REGISTRY,
)

TRUSTABLE_RESPONSE_COUNT = Counter(
    "trustable_response",
    "Trustable response count",
    labelnames=("route",),
    registry=APP_REGISTRY,
)

UNRELIABLE_RESPONSE_COUNT = Counter(
    "unreliable_response",
    "Unreliable response count",
    labelnames=("route",),
    registry=APP_REGISTRY,
)



def init_prometheus_metrics(app: FastAPI):
    INSTRUMENTATOR: Instrumentator = Instrumentator(
        should_round_latency_decimals=True,
        excluded_handlers=[
            "/metrics",
            "/docs",
            "/redoc",
            "/favicon.ico",
            "/openapi.json",
        ],
        inprogress_name="inprogress",
        inprogress_labels=True,
        registry=APP_REGISTRY,
    )
    INSTRUMENTATOR.add(metrics.default())
    INSTRUMENTATOR.instrument(app).expose(
        app, include_in_schema=False, should_gzip=True
    )
