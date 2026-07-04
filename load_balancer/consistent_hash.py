# Consistent hash ring for the load balancer (Task 2)

class ConsistentHash:

    NUM_SLOTS = 512
    VIRTUAL_SERVERS = 9  # K = log2(512)

    def __init__(self):
        # array representing the ring, each slot is None or {"server": id, "virtual": j}
        self.hash_ring = [None] * self.NUM_SLOTS

    def request_hash(self, i: int) -> int:
        # H(i) = i^2 + 2i + 17 mod M
        return (i**2 + 2 * i + 17) % self.NUM_SLOTS

    def server_hash(self, i: int, j: int) -> int:
        # Phi(i, j) = i^2 + j^2 + 2j + 25 mod M
        return (i**2 + j**2 + 2 * j + 25) % self.NUM_SLOTS

    def _find_empty_slot(self, slot: int) -> int:
        # linear probing - keep going clockwise until we find a free slot
        while self.hash_ring[slot] is not None:
            slot = (slot + 1) % self.NUM_SLOTS
        return slot

    def add_server(self, server_id: int):
        # place K virtual nodes for this server on the ring
        for j in range(self.VIRTUAL_SERVERS):
            ideal_slot = self.server_hash(server_id, j)
            actual_slot = self._find_empty_slot(ideal_slot)
            self.hash_ring[actual_slot] = {"server": server_id, "virtual": j}

    def remove_server(self, server_id: int):
        # clear all virtual nodes belonging to this server
        for slot in range(self.NUM_SLOTS):
            entry = self.hash_ring[slot]
            if entry is not None and entry["server"] == server_id:
                self.hash_ring[slot] = None

    def get_server(self, request_id: int) -> dict:
        # hash the request then walk clockwise until we hit an occupied slot
        start = self.request_hash(request_id)
        slot = start
        while self.hash_ring[slot] is None:
            slot = (slot + 1) % self.NUM_SLOTS
            if slot == start:
                raise Exception("No servers available in the ring")
        return self.hash_ring[slot]


if __name__ == "__main__":
    ring = ConsistentHash()
    ring.add_server(1)
    ring.add_server(2)
    ring.add_server(3)

    test_requests = [1001, 2456, 8765, 123456, 999999]
    for req in test_requests:
        info = ring.get_server(req)
        slot = ring.request_hash(req)
        print(f"Request {req} -> mapped slot {slot} -> assigned to {info}")

    ring.remove_server(2)
    print("\nAfter removing server 2:")
    for req in test_requests:
        info = ring.get_server(req)
        print(f"Request {req} -> {info}")
