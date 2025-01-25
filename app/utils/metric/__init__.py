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

TRUSTABLE_RESPONSE_GAUGE = Gauge(
    "trustable_response",
    "Trustable response",
    labelnames=("route",),
    registry=APP_REGISTRY,
    multiprocess_mode="livesum",
)

# useless
# REDIS_CACHE_HIT_GAUGE = Gauge(
#     "redis_cache_hit",
#     "Redis cache hit",
#     labelnames=("func",),
#     registry=APP_REGISTRY,
#     multiprocess_mode="livesum",
# )


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
