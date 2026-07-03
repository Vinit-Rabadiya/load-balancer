from flask import Flask, jsonify
from consistent_hash import ConsistentHash
import random

app = Flask(__name__)
# Initialize the consistent hash ring
hash_ring = ConsistentHash()

#list of active servers replicas
servers = [{"id": 1, "hostname": "Server1"},
    {"id": 2, "hostname": "Server2"},
    {"id": 3, "hostname": "Server3"}
]

def find_hostname(server_id):
    for server in servers:
        if server["id"] == server_id:
            return server["hostname"]
    return None

#adding three default servers to the hash ring
for server_id in range(1, 4):
    hash_ring.add_server(server_id)
    
    servers.append({
        "id": server_id,
        "hostname": f"Server{server_id}",
    })

@app.route('/rep', methods=['GET'])
def replicas():

    return jsonify({
        "message":{
            "N": len(servers),
            "replicas": [server["hostname"] for server in servers]
        },
        "status": "successful"
    }), 200

@app.route("/route", methods=["GET"])
def route_request():
    request_id = random.randint(100000, 999999)
    server_info = hash_ring.get_server(request_id)
    server_id = server_info["server"]
    hostname = find_hostname(server_id)

    return jsonify({
        "request_id": request_id,
        "server_id": server_id,
        "virtual_server": server_info["virtual"],
        "hostname": hostname
    }), 200
