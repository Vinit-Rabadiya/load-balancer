from flask import Flask, jsonify
from consistent_hash import ConsistentHash

app = Flask(__name__)
# Initialize the consistent hash ring
hash_ring = ConsistentHash()

#list of active servers replicas
servers = []

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)