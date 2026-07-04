"""
A-2: Increment N from 2 to 6, send 10000 requests at each step,
and plot average load per server as a line chart.

Before running this script the stack must be up (docker compose up).
The script calls /add and /rm to adjust the number of servers between runs.
"""

import asyncio
import aiohttp
import requests
import matplotlib.pyplot as plt
from collections import Counter

LB_BASE = "http://localhost:5000"
TOTAL_REQUESTS = 10000


async def send_requests(n_requests):
    """fire n_requests async GET /home calls, return a Counter of server_id -> count"""
    counter = Counter()

    async def fetch(session):
        try:
            async with session.get(f"{LB_BASE}/home") as resp:
                data = await resp.json()
                server_id = data["message"].split(":")[-1].strip()
                counter[server_id] += 1
        except Exception as e:
            print(f"request failed: {e}")

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[fetch(session) for _ in range(n_requests)])

    return counter


def get_current_replicas():
    resp = requests.get(f"{LB_BASE}/rep")
    return resp.json()["message"]["replicas"]


def set_server_count(target_n):
    """adjust the load balancer to have exactly target_n servers"""
    current = get_current_replicas()
    current_n = len(current)

    if current_n < target_n:
        to_add = target_n - current_n
        requests.post(f"{LB_BASE}/add", json={"n": to_add, "hostnames": []})
    elif current_n > target_n:
        to_remove = current_n - target_n
        requests.delete(f"{LB_BASE}/rm", json={"n": to_remove, "hostnames": []})

    import time
    time.sleep(2)  # give containers a moment to settle


def run():
    n_values = list(range(2, 7))  # N = 2, 3, 4, 5, 6
    avg_loads = []

    for n in n_values:
        print(f"\nsetting N={n} ...")
        set_server_count(n)

        print(f"sending {TOTAL_REQUESTS} requests ...")
        counter = asyncio.run(send_requests(TOTAL_REQUESTS))
        print(f"  distribution: {dict(counter)}")

        avg = TOTAL_REQUESTS / n
        avg_loads.append(avg)
        print(f"  average load per server: {avg:.1f}")

    return n_values, avg_loads


def plot(n_values, avg_loads):
    plt.figure(figsize=(8, 5))
    plt.plot(n_values, avg_loads, marker="o", color="steelblue", linewidth=2)

    for n, avg in zip(n_values, avg_loads):
        plt.text(n, avg + 30, f"{avg:.0f}", ha="center", fontsize=9)

    plt.title(f"A-2: Average load per server vs number of servers ({TOTAL_REQUESTS} requests each)")
    plt.xlabel("Number of servers (N)")
    plt.ylabel("Average requests per server")
    plt.xticks(n_values)
    plt.tight_layout()
    plt.savefig("a2_line_chart.png", dpi=150)
    print("saved a2_line_chart.png")
    # plt.show()  # comment out when running headless


if __name__ == "__main__":
    n_values, avg_loads = run()
    plot(n_values, avg_loads)
