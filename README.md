# Load Balancer — ICS 4104 Assignment 1

## Overview

A customizable load balancer that routes client requests across server replicas using consistent hashing. Built with Python (Flask), Docker, and the Docker SDK.

---

## Design Choices

- **Consistent hashing** is used to distribute requests. Each physical server is represented by K=9 virtual nodes on a 512-slot ring, which helps keep the load even when servers are added or removed.
- **Linear probing** resolves slot collisions when placing virtual nodes.
- **Background heartbeat monitor** runs as a daemon thread inside the load balancer, polling every server's `/heartbeat` endpoint every 5 seconds. If a server stops responding, it is deregistered from the ring and a fresh replacement container is spawned automatically.
- **Single gunicorn worker with 4 threads** (`--workers 1 --threads 4`) ensures all Flask threads share the same in-memory state (the servers dict and hash ring). Using multiple workers would give each worker its own copy of the state, which would break `/add`, `/rm`, and the monitor.
- The load balancer container is run as **privileged** so it can talk to the Docker daemon socket and spawn/remove containers at runtime.

---

## Project Structure

```
load-balancer/
├── server/
│   ├── app.py           # simple Flask server (Task 1)
│   ├── Dockerfile
│   └── requirements.txt
├── load_balancer/
│   ├── app.py           # load balancer with all endpoints (Task 3)
│   ├── consistent_hash.py  # consistent hash ring (Task 2)
│   ├── docker_manager.py   # Docker SDK wrapper
│   ├── Dockerfile
│   └── requirements.txt
├── analysis/
│   ├── a1_bar_chart.py
│   ├── a2_line_chart.py
│   ├── a3_endpoint_tests.py
│   ├── a4_modified_hash.py
│   └── requirements.txt
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## Running the Stack

```bash
make build   # build images
make up      # start all containers
make down    # stop and remove containers
make logs    # tail logs
```

Or manually:

```bash
docker compose up --build
```

The load balancer is exposed on **port 5000**.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rep` | List active replicas |
| POST | `/add` | Add N new server instances |
| DELETE | `/rm` | Remove N server instances |
| GET | `/<path>` | Route request to a server via consistent hashing |

---

## Task 4: Analysis

### A-1 — Request distribution with N=3 servers (10000 requests)

Run: `python analysis/a1_bar_chart.py`

**Observation:** With N=3 servers and K=9 virtual nodes each (27 total nodes on a 512-slot ring), the load is not perfectly even. One server may receive significantly more requests than others. This is because the specific hash functions place virtual nodes unevenly around the ring — some servers end up responsible for larger arcs of the ring than others. In our runs, server 1 consistently handled ~8400–8500 requests out of 10000, while servers 2 and 3 handled ~480 and ~1030 respectively. This is a known limitation of these hash functions and is discussed further in A-4.

The bar chart (`a1_bar_chart.png`) shows this imbalance clearly. Despite the unevenness, consistent hashing still provides the core benefit: when a server is added or removed, only the requests that were mapped to that server's arc need to be reassigned — the rest are unaffected.

---

### A-2 — Average load vs number of servers (N=2 to 6)

Run: `python analysis/a2_line_chart.py`

**Observation:** As N increases from 2 to 6, the average load per server decreases proportionally (10000/N). The line chart (`a2_line_chart.png`) shows a smooth downward curve. This confirms the load balancer scales horizontally — doubling the number of servers roughly halves the average load on each one. This is the expected behaviour of a consistent-hashing load balancer and shows the system can handle increasing client load by simply adding more replicas.

---

### A-3 — Endpoint tests and failure recovery

Run: `python analysis/a3_endpoint_tests.py`

The script tests every endpoint in sequence:

1. `GET /rep` — returns current replicas ✓
2. `POST /add` with `n=2, hostnames=["S4","S5"]` — adds two servers ✓
3. `POST /add` error case — more hostnames than `n` returns 400 ✓
4. `GET /home` — request routed to a server, returns `Hello from Server: X` ✓
5. `GET /other` — unknown path returns 400 with error message ✓
6. `DELETE /rm` with `n=3, hostnames=["S4"]` — removes S4 plus 2 randomly chosen ones ✓
7. `DELETE /rm` error case — more hostnames than `n` returns 400 ✓

**Failure recovery:** The script stops one container using the Docker SDK and then polls `/rep` every 3 seconds. Within ~10-15 seconds (the 5s heartbeat interval + time to boot a new container) the dead server disappears from the replica list and a new one appears in its place. The total count stays at N, confirming the monitor is working.

---

### A-4 — Modified hash functions

Run: `python analysis/a4_modified_hash.py`

**Modified functions:**
- `H'(i)    = i² + 3i + 11  (mod 512)`
- `Φ'(i, j) = i² + j² + 3j + 17  (mod 512)`

**Observation (A-1 equivalent):** The bar chart (`a4_bar_chart.png`) compares the two hash function sets for N=3. With the original functions, server 1 handles ~8491 requests, server 3 ~1029, and server 2 only ~480. With the modified functions the split is ~8791 / ~639 / ~570. Neither set produces a uniform distribution — server 1 dominates in both cases because its virtual node positions happen to cover the largest arc of the ring. The modified functions shift some load between servers 2 and 3, but the core skew remains.

**Observation (A-2 equivalent):** The average load (10000/N) is identical for both function sets since it is purely a function of N. However, looking at the spread (max requests − min requests across servers), the modified functions perform slightly better at higher N — the spread is 7473 vs 7713 at N=6. This shows that hash function choice affects fairness but not the theoretical average. The fundamental issue is that K=9 virtual nodes is too few to smooth out the distribution effectively. Increasing K would reduce the spread for both function sets.

---

## Assumptions

- Docker is running and the `load-balancer_lb_network` network exists before the load balancer starts.
- The server image is named `load-balancer-server` (set by `image:` tag in `docker-compose.yml`) so the load balancer can spawn copies of it at runtime.
- Server IDs are assigned sequentially from an internal counter. When a replacement is spawned after failure, it gets a new ID and a random hostname.
