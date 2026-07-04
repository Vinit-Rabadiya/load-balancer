import random
import string
import threading
import time

import requests as http_requests
from flask import Flask, jsonify, request

from consistent_hash import ConsistentHash
from docker_manager import DockerManager

app = Flask(__name__)

# hash ring and docker manager shared across all requests
hash_ring = ConsistentHash()
docker_manager = DockerManager()

# keeps track of active servers: { server_id -> {"hostname": str} }
servers: dict = {}
_lock = threading.Lock()  # need this because the monitor thread and flask threads both touch servers
_id_counter = 0


def _next_id() -> int:
    # must be called with _lock held to avoid duplicate IDs
    global _id_counter
    _id_counter += 1
    return _id_counter


def _random_hostname() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"server_{suffix}"


def _register_server(server_id: int, hostname: str):
    # add to both the servers dict and the hash ring (call with lock held)
    servers[server_id] = {"hostname": hostname}
    hash_ring.add_server(server_id)


def _deregister_server(server_id: int):
    # remove from ring first so no new requests get routed here (call with lock held)
    hash_ring.remove_server(server_id)
    del servers[server_id]


# register the 3 servers that docker-compose already started for us
with _lock:
    for _i in range(1, 4):
        _sid = _next_id()
        _register_server(_sid, f"server{_i}")


def _heartbeat_monitor():
    # background thread that checks all servers every 5 seconds
    # if a server doesn't respond, remove it and spawn a replacement to keep N constant
    while True:
        time.sleep(5)

        # take a snapshot so we don't hold the lock during the HTTP calls
        with _lock:
            snapshot = list(servers.items())

        dead = []
        for sid, info in snapshot:
            hostname = info["hostname"]
            try:
                r = http_requests.get(f"http://{hostname}:5000/heartbeat", timeout=2)
                if r.status_code != 200:
                    dead.append((sid, hostname))
            except Exception:
                dead.append((sid, hostname))

        for sid, hostname in dead:
            print(f"[monitor] {hostname} is not responding, replacing it")

            with _lock:
                if sid not in servers:
                    continue  # already handled elsewhere
                _deregister_server(sid)
                new_id = _next_id()

            new_hostname = _random_hostname()

            # boot the new container outside the lock - this can take a few seconds
            try:
                docker_manager.create_server(new_id, new_hostname)
            except Exception as e:
                print(f"[monitor] failed to start replacement: {e}")
                continue

            with _lock:
                _register_server(new_id, new_hostname)
            print(f"[monitor] started replacement {new_hostname}")


threading.Thread(target=_heartbeat_monitor, daemon=True).start()


def _replicas_list() -> list:
    # returns sorted hostname list, call with lock held
    return [servers[sid]["hostname"] for sid in sorted(servers.keys())]


@app.route("/rep", methods=["GET"])
def replicas():
    with _lock:
        return jsonify({
            "message": {
                "N": len(servers),
                "replicas": _replicas_list()
            },
            "status": "successful"
        }), 200


@app.route("/add", methods=["POST"])
def add_servers():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Request body is required", "status": "failure"}), 400

    n = data.get("n")
    hostnames = list(data.get("hostnames", []))  # copy it so we can append without touching the original

    if n is None or not isinstance(n, int) or n <= 0:
        return jsonify({"message": "<Error> 'n' must be a positive integer", "status": "failure"}), 400

    # hostname list can be shorter than n but never longer
    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than newly added instances",
            "status": "failure"
        }), 400

    # fill in random names for however many weren't specified
    while len(hostnames) < n:
        hostnames.append(_random_hostname())

    # grab all the IDs up front while holding the lock, then start containers outside it
    with _lock:
        new_ids = [_next_id() for _ in hostnames]

    for new_id, hostname in zip(new_ids, hostnames):
        try:
            docker_manager.create_server(new_id, hostname)
        except Exception as e:
            return jsonify({"message": str(e), "status": "failure"}), 500
        with _lock:
            _register_server(new_id, hostname)

    with _lock:
        return jsonify({
            "message": {
                "N": len(servers),
                "replicas": _replicas_list()
            },
            "status": "successful"
        }), 200


@app.route("/rm", methods=["DELETE"])
def remove_servers():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"message": "Request body is required", "status": "failure"}), 400

    n = data.get("n")
    hostnames = data.get("hostnames", [])

    if n is None or not isinstance(n, int) or n <= 0:
        return jsonify({"message": "<Error> 'n' must be a positive integer", "status": "failure"}), 400

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than removable instances",
            "status": "failure"
        }), 400

    with _lock:
        if n > len(servers):
            return jsonify({
                "message": "<Error> Cannot remove more servers than currently active",
                "status": "failure"
            }), 400

        # resolve named hostnames to server IDs
        named_ids = []
        for hn in hostnames:
            sid = next((s for s, info in servers.items() if info["hostname"] == hn), None)
            if sid is None:
                return jsonify({
                    "message": f"<Error> Hostname '{hn}' not found",
                    "status": "failure"
                }), 400
            named_ids.append(sid)

        # pick random ones to fill the rest of the n quota
        remaining = n - len(named_ids)
        candidates = [sid for sid in servers if sid not in named_ids]
        random_ids = random.sample(candidates, remaining)

        to_remove = named_ids + random_ids

        # grab hostnames now while we still have the lock
        to_remove_info = [(sid, servers[sid]["hostname"]) for sid in to_remove]

        # deregister from the ring immediately so requests stop going there
        for sid in to_remove:
            _deregister_server(sid)

    # stop the actual containers outside the lock since it's slow
    for sid, hostname in to_remove_info:
        try:
            docker_manager.remove_server(hostname)
        except Exception:
            pass

    with _lock:
        return jsonify({
            "message": {
                "N": len(servers),
                "replicas": _replicas_list()
            },
            "status": "successful"
        }), 200


@app.route("/<path:path>", methods=["GET"])
def route_request(path):
    # pick a random request ID and use consistent hashing to find the target server
    request_id = random.randint(100000, 999999)

    with _lock:
        if not servers:
            return jsonify({"message": "<Error> No server replicas available", "status": "failure"}), 503
        server_info = hash_ring.get_server(request_id)
        hostname = servers[server_info["server"]]["hostname"]

    try:
        resp = http_requests.get(f"http://{hostname}:5000/{path}", timeout=5)
    except http_requests.RequestException as e:
        return jsonify({"message": f"<Error> Could not reach server: {e}", "status": "failure"}), 500

    # if the path doesn't exist on the server, return the assignment-specified error format
    if resp.status_code == 404:
        return jsonify({
            "message": f"<Error> '/{path}' endpoint does not exist in server replicas",
            "status": "failure"
        }), 400

    try:
        body = resp.json()
    except Exception:
        body = {"message": resp.text, "status": "failure"}

    return jsonify(body), resp.status_code
