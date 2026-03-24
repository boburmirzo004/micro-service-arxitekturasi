import logging
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request, Response, HTTPException
import httpx

from load_balancer.settings import settings
from load_balancer.algorithms import LoadBalancer
from load_balancer.health_check import HealthChecker
from load_balancer.circuit_breaker import CircuitBreaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_balancer = LoadBalancer(settings.BACKEND_SERVICES, weights=settings.SERVICE_WEIGHTS)
health_checker = HealthChecker(load_balancer)
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_time=30, slow_threshold=2.0)

http_client = httpx.AsyncClient(timeout=30.0)

# oddiy in-memory metrikalar
_metrics = {
    "total_requests": 0,
    "total_errors": 0,
    "latencies": [],
    "per_service": {},
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Load Balancer ishga tushdi")
    logger.info(f"Servislar: {settings.BACKEND_SERVICES}")
    logger.info(f"Algoritm: {settings.LB_ALGORITHM}")
    health_checker.start()
    yield
    logger.info("Load Balancer toxtadi")
    health_checker.stop()
    await http_client.aclose()


app = FastAPI(lifespan=lifespan, title="Load Balancer")

@app.get("/stats")
async def get_lb_stats():
    stats = load_balancer.get_stats()
    latencies = list(_metrics["latencies"])
    avg_latency = 0

    if latencies:
        avg_latency = sum(latencies) / len(latencies)

    return {
        "status": "online",
        "algorithm": settings.LB_ALGORITHM,
        "healthy_services": stats["healthy_services"],
        "active_connections": stats["active_connections"],
        "total_requests": _metrics["total_requests"],
        "total_errors": _metrics["total_errors"],
        "average_latency": avg_latency,
        "per_service_metrics": _metrics["per_service"]
    }

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def proxy(request: Request, path: str):
    _metrics["total_requests"] += 1

    start_time = perf_counter()

    headers = dict(request.headers)
    headers.pop("host", None)

    body = await request.body()

    last_error: Exception | None = None

    for attempt in range(settings.MAX_RETRY_ATTEMPTS + 1):
        target_service = load_balancer.get_next_service(settings.LB_ALGORITHM)
        if not target_service:
            _metrics["total_errors"] += 1
            raise HTTPException(status_code=503, detail="Hech bir soglom servis yoq")

        # circuit ochiqmi tekshiramiz
        if circuit_breaker.is_open(target_service):
            logger.info(f"{target_service} blokda, otkazib yuborildi")
            continue

        url = f"{target_service}/{path}"

        try:
            load_balancer.increment_connection(target_service)
            logger.info(f"Proxying {request.method} /{path} -> {target_service} (urinish {attempt + 1})")

            response = await http_client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                params=request.query_params,
            )

            duration = perf_counter() - start_time
            _metrics["latencies"].append(duration)
            if len(_metrics["latencies"]) > settings.METRICS_WINDOW:
                _metrics["latencies"].pop(0)

            # servis boyicha metrikalarni yangilaymiz
            svc_m = _metrics["per_service"].setdefault(
                target_service, {"total": 0, "slow": 0}
            )
            svc_m["total"] += 1
            if duration > 1.0:
                svc_m["slow"] += 1

            circuit_breaker.record_slow(target_service, duration)
            circuit_breaker.record_success(target_service)

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
        except httpx.RequestError as e:
            circuit_breaker.record_failure(target_service)
            last_error = e
            _metrics["total_errors"] += 1
            logger.error(f"Xato: {target_service} bilan aloqa muammo: {e}")
        finally:
            load_balancer.decrement_connection(target_service)

    raise HTTPException(status_code=502, detail=f"Bad Gateway: {last_error}")