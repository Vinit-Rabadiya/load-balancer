import docker
import time
import requests as http_requests

# these match what's defined in docker-compose.yml
NETWORK_NAME = "load-balancer_lb_network"
SERVER_IMAGE = "load-balancer-server"


class DockerManager:

    def __init__(self):
        self.client = docker.from_env()

    def create_server(self, server_id: int, hostname: str):
        # start the container and wait for it to be ready before returning
        container = self.client.containers.run(
            image=SERVER_IMAGE,
            name=hostname,
            hostname=hostname,
            detach=True,
            network=NETWORK_NAME,
            environment={"SERVER_ID": str(server_id)},
        )
        self._wait_until_ready(hostname)
        return container

    def _wait_until_ready(self, hostname: str, timeout: int = 30):
        # poll /heartbeat until we get a 200 back or we time out
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                r = http_requests.get(f"http://{hostname}:5000/heartbeat", timeout=2)
                if r.status_code == 200:
                    return
            except Exception:
                pass
            time.sleep(1)
        raise TimeoutError(f"Server {hostname} did not become ready in {timeout}s")

    def remove_server(self, hostname: str):
        try:
            container = self.client.containers.get(hostname)
            container.stop()
            container.remove()
        except docker.errors.NotFound:
            pass  # container already gone, nothing to do
