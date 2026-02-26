from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Port to run the load balancer on
    PORT: int = 8000
    
    # List of backend services that we are balancing
    BACKEND_SERVICES: List[str] = [
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8002",
        "http://127.0.0.1:8003"
    ]
    
    # Services weights (used for weighted_round_robin)
    # Higher weight = more traffic
    SERVICE_WEIGHTS: dict = {
        "http://127.0.0.1:8001": 3,
        "http://127.0.0.1:8002": 2,
        "http://127.0.0.1:8003": 1
    }
    
    # Load balancing algorithm to use (round_robin, random, least_connections, weighted_round_robin)
    LB_ALGORITHM: str = "round_robin"
    
    # Health check interval in seconds
    HEALTH_CHECK_INTERVAL: int = 5
    
    class Config:
        env_file = ".env"

settings = Settings()
