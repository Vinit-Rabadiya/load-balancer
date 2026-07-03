class ConsistentHash:
    def __init__(self):
        self.num_slots = 512
        self.virtual_servers = 9

        #Represents the hash ring
        self.hash_ring = [None] * self.num_slots

    def server_hash(self, server_id, virtual_id):
        """
        Hashes the server ID and virtual ID to a position on the hash ring.
        """
        return (server_id**2 + virtual_id**2 + 2*virtual_id + 25) % self.num_slots
    
    def find_empty_slot(self, slot):
        while self.hash_ring[slot] is not None:
            slot = (slot + 1) % self.num_slots
        return slot
    
    def add_server(self, server_id):
        for virtual_id in range(self.virtual_servers):
            slot = self.server_hash(server_id, virtual_id)
            empty_slot = self.find_empty_slot(slot)
            self.hash_ring[empty_slot] = {
                "server": server_id,
                "virtual": virtual_id
            }
    def request_hash(self, request_id):
        """
        Hashes the request ID to a position on the hash ring and finds the corresponding server.
        """
        return (request_id**2 + 2*request_id + 17) % self.num_slots
    
    def get_server(self, request_id):
        """
        Given a request ID, finds the corresponding server on the hash ring.
        """
        slot = self.request_hash(request_id)
        start_slot = slot
        while self.hash_ring[slot] is None:
            slot = (slot + 1) % self.num_slots
            if slot == start_slot:
                raise Exception("No servers available")
        return self.hash_ring[slot]



if __name__ == "__main__":

    ring = ConsistentHash()

    ring.add_server(1)
    ring.add_server(2)
    ring.add_server(3)

    test_requests = [1001, 2456, 8765, 123456, 999999]

    for request in test_requests:
        server = ring.get_server(request)
        slot = ring.request_hash(request)

        print(f"Request {request} -> Slot {slot} -> Server {server}")