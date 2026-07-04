"""
A-4: Repeat A-1 and A-2 observations with modified hash functions and compare.

Modified functions (simple alternatives to see the effect on distribution):
  H'(i)    = i^2 + 3i + 11   (mod M)
  Phi'(i,j)= i^2 + j^2 + 3j + 17  (mod M)

We run the same simulation as A-1 and A-2 but purely offline (using the
ConsistentHash class directly with random request IDs) so we don't need
the Docker stack for this comparison.
"""

import sys
import os
import random
import matplotlib.pyplot as plt
from collections import Counter

# add the load_balancer folder so we can import ConsistentHash directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "load_balancer"))
from consistent_hash import ConsistentHash

TOTAL_REQUESTS = 10000
N_DEFAULT = 3


# --- modified hash ring subclass ---

class ConsistentHashModified(ConsistentHash):
    # modified hash functions for A-4
    def request_hash(self, i: int) -> int:
        # H'(i) = i^2 + 3i + 11 mod M
        return (i**2 + 3 * i + 11) % self.NUM_SLOTS

    def server_hash(self, i: int, j: int) -> int:
        # Phi'(i, j) = i^2 + j^2 + 3j + 17 mod M
        return (i**2 + j**2 + 3 * j + 17) % self.NUM_SLOTS


# --- simulation helpers ---

def simulate_distribution(ring_class, n_servers, n_requests):
    """build a ring with n_servers and simulate n_requests, return Counter"""
    ring = ring_class()
    for i in range(1, n_servers + 1):
        ring.add_server(i)

    counter = Counter()
    for _ in range(n_requests):
        req_id = random.randint(100000, 999999)
        server = ring.get_server(req_id)["server"]
        counter[server] += 1

    return counter


# --- A-4 version of A-1: bar chart for N=3, original vs modified ---

def a4_bar_chart():
    orig_counter = simulate_distribution(ConsistentHash, N_DEFAULT, TOTAL_REQUESTS)
    mod_counter  = simulate_distribution(ConsistentHashModified, N_DEFAULT, TOTAL_REQUESTS)

    servers = sorted(set(orig_counter.keys()) | set(mod_counter.keys()))
    x = range(len(servers))
    width = 0.35

    orig_counts = [orig_counter[s] for s in servers]
    mod_counts  = [mod_counter[s]  for s in servers]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars1 = ax.bar([i - width/2 for i in x], orig_counts, width, label="Original H, Phi", color="steelblue", edgecolor="black")
    bars2 = ax.bar([i + width/2 for i in x], mod_counts,  width, label="Modified H', Phi'", color="salmon",    edgecolor="black")

    for bar, val in zip(bars1, orig_counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 30,
                str(val), ha="center", va="bottom", fontsize=8)
    for bar, val in zip(bars2, mod_counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 30,
                str(val), ha="center", va="bottom", fontsize=8)

    ax.set_title(f"A-4 (A-1 equivalent): distribution with N=3, {TOTAL_REQUESTS} requests")
    ax.set_xlabel("Server ID")
    ax.set_ylabel("Requests handled")
    ax.set_xticks(list(x))
    ax.set_xticklabels([str(s) for s in servers])
    ax.legend()
    plt.tight_layout()
    plt.savefig("a4_bar_chart.png", dpi=150)
    print("saved a4_bar_chart.png")
    # plt.show()  # comment out when running headless


# --- A-4 version of A-2: average load line chart, original vs modified ---

def a4_line_chart():
    n_values = list(range(2, 7))
    orig_avgs = []
    mod_avgs  = []

    for n in n_values:
        orig_counter = simulate_distribution(ConsistentHash, n, TOTAL_REQUESTS)
        mod_counter  = simulate_distribution(ConsistentHashModified, n, TOTAL_REQUESTS)

        # average load = total requests / number of servers
        orig_avgs.append(TOTAL_REQUESTS / n)
        mod_avgs.append(TOTAL_REQUESTS / n)

        # also show actual distribution spread for reference
        orig_spread = max(orig_counter.values()) - min(orig_counter.values())
        mod_spread  = max(mod_counter.values())  - min(mod_counter.values())
        print(f"N={n}  orig spread={orig_spread}  modified spread={mod_spread}")
        print(f"      orig={dict(orig_counter)}")
        print(f"      mod ={dict(mod_counter)}")

    plt.figure(figsize=(9, 5))
    plt.plot(n_values, orig_avgs, marker="o", label="Original",  color="steelblue", linewidth=2)
    plt.plot(n_values, mod_avgs,  marker="s", label="Modified",  color="salmon",    linewidth=2, linestyle="--")
    plt.title(f"A-4 (A-2 equivalent): average load per server, {TOTAL_REQUESTS} requests each")
    plt.xlabel("Number of servers (N)")
    plt.ylabel("Average requests per server")
    plt.xticks(n_values)
    plt.legend()
    plt.tight_layout()
    plt.savefig("a4_line_chart.png", dpi=150)
    print("saved a4_line_chart.png")
    # plt.show()  # comment out when running headless


if __name__ == "__main__":
    print("=== A-4: Modified hash functions comparison ===\n")
    a4_bar_chart()
    a4_line_chart()
