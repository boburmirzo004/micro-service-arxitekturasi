import random
from typing import List, Dict

class LoadBalancer:
    def __init__(self, services: List[str], weights: Dict[str, int] = None):
        self.services = services
        self.weights = weights or {}
        self._current_index = 0
        self._weighted_index = 0
        self._weighted_pool = []
        self._connections = {service: 0 for service in services}
        self._build_weighted_pool()

    def _build_weighted_pool(self):
        """Build a pool for weighted round robin based on configured weights"""
        self._weighted_pool = []
        # Filter weights for only currently available healthy services
        for service in self.services:
            weight = self.weights.get(service, 1) # default weight is 1
            self._weighted_pool.extend([service] * weight)
        
        # Shuffle to distribute evenly if you want, but standard WRR is sequential
        # We'll leave it as is for deterministic WRR demo

    def update_services(self, healthy_services: List[str]):
        """Update the list of available services from health checker"""
        if self.services != healthy_services:
            self.services = healthy_services
            self._build_weighted_pool()
            self._weighted_index = 0
            self._current_index = 0
            
            # Keep track of connections for new services if doing least_connections
            for s in self.services:
                if s not in self._connections:
                    self._connections[s] = 0

    def get_next_service_round_robin(self) -> str:
        if not self.services:
            return None
        service = self.services[self._current_index % len(self.services)]
        self._current_index = (self._current_index + 1) % len(self.services)
        return service

    def get_next_service_weighted_round_robin(self) -> str:
        if not self._weighted_pool:
            return self.get_next_service_round_robin()
            
        service = self._weighted_pool[self._weighted_index % len(self._weighted_pool)]
        self._weighted_index = (self._weighted_index + 1) % len(self._weighted_pool)
        return service

    def get_next_service_random(self) -> str:
        if not self.services:
            return None
        return random.choice(self.services)

    def get_next_service_least_connections(self) -> str:
        if not self.services:
            return None
        
        # Filter connections dictionary for only currently healthy services
        active_conns = {s: self._connections.get(s, 0) for s in self.services}
        
        # Find the minimum value
        min_conns = min(active_conns.values())
        
        # Get all services that have this minimum value
        min_services = [s for s, count in active_conns.items() if count == min_conns]
        
        # Pick one at random if there's a tie
        selected_service = random.choice(min_services)
        return selected_service

    def get_next_service(self, algorithm: str = "round_robin") -> str:
        """Main method to get the next backend server based on specified algorithm"""
        if not self.services:
            return None
            
        if algorithm == "random":
            return self.get_next_service_random()
        elif algorithm == "least_connections":
            return self.get_next_service_least_connections()
        elif algorithm == "weighted_round_robin":
            return self.get_next_service_weighted_round_robin()
        else:
            return self.get_next_service_round_robin()
            
    def get_stats(self) -> dict:
        """Return current status of the load balancer for monitoring"""
        return {
            "healthy_services": self.services,
            "active_connections": self._connections,
            "weighted_pool_size": len(self._weighted_pool),
            "total_services_configured": len(self._connections)
        }

    def increment_connection(self, service: str):
        if service in self._connections:
            self._connections[service] += 1
            
    def decrement_connection(self, service: str):
        if service in self._connections and self._connections[service] > 0:
            self._connections[service] -= 1
