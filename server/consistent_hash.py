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

if __name__ == "__main__":

    ring = ConsistentHash()

    ring.add_server(1)
    ring.add_server(2)
    ring.add_server(3)

    for slot, server in enumerate(ring.hash_ring):
        if server:
            print(f"Slot {slot}: {server}")