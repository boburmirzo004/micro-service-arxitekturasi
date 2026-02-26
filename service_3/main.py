from fastapi import FastAPI
import socket
import os
import random
import asyncio

app = FastAPI()

SERVICE_NAME = os.getenv("SERVICE_NAME", "Service 3")

@app.get("/")
async def read_root():
    delay = random.uniform(0.1, 0.3)
    await asyncio.sleep(delay)
    
    return {
        "service": SERVICE_NAME,
        "hostname": socket.gethostname(),
        "delay_simulated": f"{delay:.2f}s",
        "status": "success"
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": SERVICE_NAME}