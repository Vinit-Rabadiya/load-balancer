from flask import Flask, jsonify
from consistent_hash import ConsistentHash
import random
import requests

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