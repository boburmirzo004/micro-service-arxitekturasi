import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException
import httpx

from .settings import settings
from .algorithms import LoadBalancer
from .health_check import HealthChecker

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
load_balancer = LoadBalancer(settings.BACKEND_SERVICES, weights=settings.SERVICE_WEIGHTS)
health_checker = HealthChecker(load_balancer)

# Shared HTTP client for proxying
http_client = httpx.AsyncClient(timeout=30.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start health checker
    logger.info("Starting Load Balancer...")
    logger.info(f"Configured services: {settings.BACKEND_SERVICES}")
    logger.info(f"Algorithm: {settings.LB_ALGORITHM}")
    health_checker.start()
    
    yield
    
    # Shutdown: Stop health checker and close HTTP client
    logger.info("Shutting down Load Balancer...")
    health_checker.stop()
    await http_client.aclose()


app = FastAPI(lifespan=lifespan, title="Professional Load Balancer")

@app.get("/stats")
async def get_lb_stats():
    """Monitoring endpoint to see the load on each server"""
    stats = load_balancer.get_stats()
    return {
        "status": "online",
        "algorithm": settings.LB_ALGORITHM,
        "details": stats,
        "weights": settings.SERVICE_WEIGHTS
    }

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def proxy(request: Request, path: str):
    # Determine the target service using the configured algorithm
    target_service = load_balancer.get_next_service(settings.LB_ALGORITHM)
    
    if not target_service:
        raise HTTPException(status_code=503, detail="No healthy upstream services available")
        
    # Construct the full URL for the backend service
    url = f"{target_service}/{path}"
    
    # We don't want to pass the host header from the original request
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # Read the body of the incoming request
    body = await request.body()
    
    try:
        # Track connection start (for least_connections algorithm)
        load_balancer.increment_connection(target_service)
        
        logger.info(f"Proxying {request.method} /{path} to {target_service}")
        
        # Forward the request to the upstream service
        response = await http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            params=request.query_params
        )
        
        # Return the response to the client
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except httpx.RequestError as e:
        logger.error(f"Error communicating with upstream {target_service}: {e}")
        # Mark as potentially unhealthy immediately, health checker will confirm soon
        raise HTTPException(status_code=502, detail="Bad Gateway")
    finally:
        # Track connection end (for least_connections algorithm)
        load_balancer.decrement_connection(target_service)