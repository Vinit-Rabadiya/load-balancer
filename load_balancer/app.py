from flask import Flask, jsonify, request
from consistent_hash import ConsistentHash
import random
import requests
from docker_manager import DockerManager

app = Flask(__name__)
# Initialize the consistent hash ring
hash_ring = ConsistentHash()

#list of active servers replicas
servers = {}

#adding three default servers to the hash ring
for server_id in range(1, 4):
    hash_ring.add_server(server_id)
    
    servers[server_id] = {
        "hostname": f"server{server_id}"
    }

@app.route('/rep', methods=['GET'])
def replicas():

    return jsonify({
        "message":{
            "N": len(servers),
            "replicas": [server["hostname"] for server in servers.values()]
        },
        "status": "successful"
    }), 200

@app.route("/route", methods=["GET"])
def route_request():
    request_id = random.randint(100000, 999999)
    server_info = hash_ring.get_server(request_id)
    server_id = server_info["server"]

    return jsonify({
        "request_id": request_id,
        "server_id": server_id,
        "virtual_server": server_info["virtual"],
    }), 200

@app.route("/home", methods=["GET"])
def forward_home():

    # Generate a random request ID
    request_id = random.randint(100000, 999999)

    # Find which server should handle it
    server_info = hash_ring.get_server(request_id)

    server_id = server_info["server"]

    hostname = servers[server_id]["hostname"]

    # Forward the request
    try:
        response = requests.get(f"http://{hostname}:5000/home")
    except requests.RequestException:
        # Return the server's response
        return jsonify(response.json()), response.status_code
    
docker_manager = DockerManager()

@app.route("/docker-test")
def docker_test():

    return {
        "containers": docker_manager.list_running_containers()
    }

@app.route("/add", methods=["POST"])
def add_servers():

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required",
            "status": "failure"
        }), 400

    n = data.get("n")
    hostnames = data.get("hostnames")

    if n is None or hostnames is None:
        return jsonify({
            "message": "Both 'n' and 'hostnames' are required.",
            "status": "failure"
        }), 400

    if len(hostnames) != n:
        return jsonify({
            "message": "Length of hostnames must equal n.",
            "status": "failure"
        }), 400

    next_server_id = max(servers.keys()) + 1

    for hostname in hostnames:

        # Create Docker container (we'll improve this later)
        try:
            docker_manager.create_server(next_server_id, hostname)
        except Exception as e:
            return jsonify({
                "message": str(e),
                "status": "failure"
            }), 500

        servers[next_server_id] = {
            "hostname": hostname,
            "status": "healthy"
        }

        hash_ring.add_server(next_server_id)

        next_server_id += 1

    replicas = [
        servers[sid]["hostname"]
        for sid in sorted(servers.keys())
    ]

    return jsonify({
        "message": {
            "N": len(servers),
            "replicas": replicas
        },
        "status": "successful"
    }), 200

@app.route("/rm", methods=["DELETE"])
def remove_servers():

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required",
            "status": "failure"
        }), 400

    hostnames = data.get("hostnames")

    if not hostnames:
        return jsonify({
            "message": "hostnames are required",
            "status": "failure"
        }), 400

    removed = 0

    for hostname in hostnames:

        server_id = None

        for sid, info in servers.items():
            if info["hostname"] == hostname:
                server_id = sid
                break

        if server_id is None:
            continue

        try:
            docker_manager.remove_server(hostname)
        except Exception:
            pass

        hash_ring.remove_server(server_id)

        del servers[server_id]

        removed += 1

    replicas = [
        servers[sid]["hostname"]
        for sid in sorted(servers.keys())
    ]

    return jsonify({
        "message": {
            "N": len(servers),
            "replicas": replicas
        },
        "status": "successful"
    }), 200