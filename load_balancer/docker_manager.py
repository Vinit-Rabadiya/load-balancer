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

    def create_server(self, server_id):

        name = f"server{server_id}"

        container = self.client.containers.run(
            image="load-balancer-server",
            name=name,
            detach=True,
            network="load-balancer_lb_network",
            environment={
                "SERVER_ID": str(server_id)
            }
        )

        return container