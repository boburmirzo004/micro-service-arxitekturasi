from fastapi import FastAPI
import socket
import os
import random
import asyncio

app = FastAPI()

# Shunchaki servis ismini olish (Docker yoki local portdan oson farqlash uchun)
SERVICE_NAME = os.getenv("SERVICE_NAME", "Service 1")

@app.get("/")
async def read_root():
    # Professional demo uchun yuklanishni imitatsiya qilamiz
    # Tasodifiy kutish vaqti (0.1 soniyadan 0.3 gacha)
    delay = random.uniform(0.1, 0.3)
    await asyncio.sleep(delay)
    
    return {
        "service": SERVICE_NAME,
        "hostname": socket.gethostname(),
        "delay_simulated": f"{delay:.2f}s",
        "status": "success"
    }

# Health Check yo'li - bu Load Balancer uchun juda muhim!
@app.get("/health")
def health_check():
    return {"status": "ok", "service": SERVICE_NAME}