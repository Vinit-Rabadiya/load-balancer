import docker
import time

class DockerManager:

    def __init__(self):
        self.client = docker.from_env()

    def list_running_containers(self):
        return [
            container.name
            for container in self.client.containers.list()
        ]

    def create_server(self, server_id, hostname):

        hostname = f"server{server_id}"

        container = self.client.containers.run(
            image="load-balancer-server",
            name=hostname,
            hostname=hostname,
            detach=True,
            network="load-balancer_lb_network",
            environment={
                "SERVER_ID": str(server_id)
            }
        )
        self.wait_until_healthy(container)
        return container
    
    def wait_until_healthy(self, container):

        while True:

            container.reload()

            health = container.attrs["State"].get("Health")

            if health and health["Status"] == "healthy":
                return True

            time.sleep(1)
            
    def remove_server(self, hostname):
        container = self.client.containers.get(hostname)
        container.stop()
        container.remove()