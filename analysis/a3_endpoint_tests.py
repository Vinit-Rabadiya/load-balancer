"""
A-3: Test all load balancer endpoints and demonstrate failure recovery.

Runs through:
  1. GET  /rep        - check replica status
  2. POST /add        - add new servers
  3. GET  /home       - route a request
  4. GET  /other      - invalid path (should return 400)
  5. DELETE /rm       - remove servers
  6. Failure recovery - manually stop a server container and confirm the
                        load balancer spawns a replacement
"""

import requests
import docker
import time

LB_BASE = "http://localhost:5000"


def section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print('='*55)


def show(resp):
    print(f"  status : {resp.status_code}")
    try:
        print(f"  body   : {resp.json()}")
    except Exception:
        print(f"  body   : {resp.text}")


# 1. GET /rep
section("1. GET /rep - check current replicas")
resp = requests.get(f"{LB_BASE}/rep")
show(resp)

# 2. POST /add - add 2 servers with specific hostnames
section("2. POST /add - add 2 servers (S4, S5)")
resp = requests.post(f"{LB_BASE}/add", json={"n": 2, "hostnames": ["S4", "S5"]})
show(resp)

# 2b. POST /add - error case: more hostnames than n
section("2b. POST /add - error: hostnames list longer than n")
resp = requests.post(f"{LB_BASE}/add", json={"n": 1, "hostnames": ["S6", "S7"]})
show(resp)

# 3. GET /rep - confirm servers were added
section("3. GET /rep - confirm state after /add")
resp = requests.get(f"{LB_BASE}/rep")
show(resp)

# 4. GET /home - valid path, should route to a server
section("4. GET /home - valid route")
resp = requests.get(f"{LB_BASE}/home")
show(resp)

# 5. GET /other - invalid path
section("5. GET /other - invalid path (expect 400)")
resp = requests.get(f"{LB_BASE}/other")
show(resp)

# 6. DELETE /rm - remove with specific + random selection
section("6. DELETE /rm - remove 3 servers (S4 named, 2 random)")
resp = requests.delete(f"{LB_BASE}/rm", json={"n": 3, "hostnames": ["S4"]})
show(resp)

# 6b. DELETE /rm - error case: more hostnames than n
section("6b. DELETE /rm - error: hostnames list longer than n")
resp = requests.delete(f"{LB_BASE}/rm", json={"n": 1, "hostnames": ["S5", "extra"]})
show(resp)

# 7. GET /rep - confirm final state
section("7. GET /rep - final replica state")
resp = requests.get(f"{LB_BASE}/rep")
show(resp)

# 8. Failure recovery test
section("8. Failure recovery - kill a server container and wait for replacement")

# get the current replicas so we know which one to kill
current = requests.get(f"{LB_BASE}/rep").json()["message"]["replicas"]
print(f"  current replicas: {current}")

if current:
    victim = current[0]
    print(f"  stopping container: {victim}")

    client = docker.from_env()
    try:
        container = client.containers.get(victim)
        container.stop()
        print(f"  container {victim} stopped")
    except Exception as e:
        print(f"  could not stop container: {e}")
        exit(1)

    # poll /rep until a replacement appears (or timeout after 60s)
    print("  waiting for load balancer to detect failure and spawn replacement ...")
    timeout = 60
    start = time.time()
    replaced = False

    while time.time() - start < timeout:
        time.sleep(3)
        resp = requests.get(f"{LB_BASE}/rep")
        replicas = resp.json()["message"]["replicas"]
        print(f"  [{int(time.time()-start)}s] replicas: {replicas}")

        if victim not in replicas and len(replicas) >= len(current):
            print(f"  replacement detected! new replica set: {replicas}")
            replaced = True
            break

    if not replaced:
        print(f"  WARNING: replacement not detected within {timeout}s")
else:
    print("  no replicas running, skipping failure test")
