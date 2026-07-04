"""
A-1: Send 10000 async requests to N=3 servers and plot a bar chart
of how many requests each server handled.
"""

import asyncio
import aiohttp
import matplotlib.pyplot as plt
from collections import Counter

LB_URL = "http://localhost:5000/home"
TOTAL_REQUESTS = 10000


async def send_request(session, counter):
    try:
        async with session.get(LB_URL) as resp:
            data = await resp.json()
            # message is "Hello from Server: X" - grab the server id at the end
            server_id = data["message"].split(":")[-1].strip()
            counter[server_id] += 1
    except Exception as e:
        print(f"request failed: {e}")


async def run():
    counter = Counter()
    async with aiohttp.ClientSession() as session:
        tasks = [send_request(session, counter) for _ in range(TOTAL_REQUESTS)]
        await asyncio.gather(*tasks)
    return counter


def plot(counter):
    servers = sorted(counter.keys())
    counts = [counter[s] for s in servers]

    plt.figure(figsize=(8, 5))
    bars = plt.bar(servers, counts, color="steelblue", edgecolor="black")

    # label each bar with its count
    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 50,
                 str(count), ha="center", va="bottom", fontsize=10)

    plt.title(f"A-1: Request distribution across N=3 servers ({TOTAL_REQUESTS} requests)")
    plt.xlabel("Server ID")
    plt.ylabel("Number of requests handled")
    plt.tight_layout()
    plt.savefig("a1_bar_chart.png", dpi=150)
    print("saved a1_bar_chart.png")
    # plt.show()  # comment out when running headless


if __name__ == "__main__":
    print(f"sending {TOTAL_REQUESTS} async requests to {LB_URL} ...")
    counter = asyncio.run(run())
    print("results:", dict(counter))
    plot(counter)
