from flask import Flask, jsonify
import os

app = Flask(__name__)

# get server ID from environment variable set when the container is started
SERVER_ID = os.getenv('SERVER_ID', 'unknown')

@app.route('/home', methods=['GET'])
def home():
    return jsonify({
        'message': f'Hello from Server: {SERVER_ID}',
        'status': 'successful'
    }), 200

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    # just return 200 so the load balancer knows we're alive
    return '', 200
