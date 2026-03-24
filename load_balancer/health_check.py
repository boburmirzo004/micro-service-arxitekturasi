import asyncio
import httpx
import logging
from typing import List
from load_balancer.settings import settings
from load_balancer.algorithms import LoadBalancer

logger = logging.getLogger(__name__)

class HealthChecker:
    def __init__(self, load_balancer: LoadBalancer):
        self.load_balancer = load_balancer
        self.all_services = settings.BACKEND_SERVICES
        self.healthy_services = list(self.all_services)
        self.is_running = False

    async def check_service(self, service_url: str) -> bool:
        try:
            health_url = f"{service_url}/health"
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(health_url)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed for {service_url}: {e}")
            return False

    async def run_checks(self):
        while self.is_running:
            current_healthy = []
            tasks = [self.check_service(service) for service in self.all_services]
            results = await asyncio.gather(*tasks)
            for service, is_healthy in zip(self.all_services, results):
                if is_healthy:
                    current_healthy.append(service)
            if current_healthy != self.healthy_services:
                logger.info(f"Healthy services updated: {current_healthy}")
                self.healthy_services = current_healthy
                self.load_balancer.update_services(self.healthy_services)
            await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL)

    def start(self):
        if not self.is_running:
            self.is_running = True
            asyncio.create_task(self.run_checks())
            logger.info("Health checker started")

    def stop(self):
        self.is_running = False
        logger.info("Health checker stopped")
