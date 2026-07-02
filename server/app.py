from flask import Flask, jsonify
import os

app = Flask(__name__)

SERVER_ID = os.getenv('SERVER_ID', 'unknown')
@app.route('/home', methods=['GET'])
def home():
    return jsonify({'message': f'Hello from server {SERVER_ID}!',
                    "status": 'success'}), 200

@app.route("/heartbeat", methods=['GET'])
def heartbeat():
    return jsonify({'message': f'Server {SERVER_ID} is alive!',
                    "status": 'success'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)