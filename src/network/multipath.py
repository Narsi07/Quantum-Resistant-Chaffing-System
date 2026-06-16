import random
import time
import logging

class MultiPathRouter:
    """
    Simulates splitting traffic across multiple paths to mitigate traffic analysis.
    Different paths might have different latencies.
    """
    def __init__(self, num_paths=3):
        self.num_paths = num_paths
        self.paths = [{"id": i, "latency_mean": 0.05 * (i+1), "latency_sigma": 0.01} for i in range(num_paths)]

    def route_packet(self, data):
        """
        Selects a path for the packet.
        Returns: (path_id, simulated_latency)
        """
        # Simple policy: Random or Round Robin. Let's use weighted random based on current 'load' (simulated)
        path = random.choice(self.paths)
        
        # Simulate latency jitter
        latency = random.gauss(path["latency_mean"], path["latency_sigma"])
        latency = max(0.001, latency)
        
        logging.info(f"Routing packet via Path {path['id']} (Latency: {latency*1000:.1f}ms)")
        return path["id"], latency

    def reorder_packets(self, received_packets):
        """
        Reorders packets based on sequence number (simulated).
        Params:
            received_packets: List of (seq_num, data) tuples
        Returns:
            Sorted list of data
        """
        sorted_pkts = sorted(received_packets, key=lambda x: x[0])
        return [pkt[1] for pkt in sorted_pkts]
