from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # 0.0.0.0 qilib qo'ysak tarmoqdan ham kirsa bo'ladi
    HOST: str = "0.0.0.0"

    PORT: int = 8000
    
    # backend servislar ro'yxati
    BACKEND_SERVICES: List[str] = [
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8002",
        "http://127.0.0.1:8003"
    ]
    
    # weighted round robin uchun vaznlar
    SERVICE_WEIGHTS: dict = {
        "http://127.0.0.1:8001": 3,
        "http://127.0.0.1:8002": 2,
        "http://127.0.0.1:8003": 1
    }
    
    LB_ALGORITHM: str = "round_robin"
    HEALTH_CHECK_INTERVAL: int = 5

    # xato bolsa necha marta qayta urinadi
    MAX_RETRY_ATTEMPTS: int = 2

    METRICS_WINDOW: int = 1000
    
    class Config:
        env_file = ".env"

settings = Settings()
