import time
import socket
import random

# Target address matching receiver default
UDP_IP = "127.0.0.1"
UDP_PORT = 4210

# MAC addresses updated from anchor_config.csv
ANCHOR_MACS = [
    "68:fe:71:8b:45:b6",  # Anchor_A (0.0, 0.0)
    "68:fe:71:8b:4c:6e",  # Anchor_B (0.0, 4.0)
    "00:4b:12:9a:f9:3e",  # Anchor_C (4.0, 0.0)
    "20:e7:c8:69:2a:5a",  # Anchor_D (4.0, 4.0)
]

TARGETS = ["T1", "T2", "T3"]

def generate_mock_rssi(base_rssi=-60, noise_level=3, outlier_chance=0.1):
    """Generates realistic RSSI readings with Gaussian noise and occasional spikes."""
    if random.random() < outlier_chance:
        return random.randint(-85, -40)
    return int(random.gauss(base_rssi, noise_level))

def run_simulation():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"[Simulated Targets] Broadcasting mock BLE packets for {TARGETS} to {UDP_IP}:{UDP_PORT}...")
    
    try:
        while True:
            for target_id in TARGETS:
                for mac in ANCHOR_MACS:
                    rssi = generate_mock_rssi()
                    packet = f"{target_id},{mac},{rssi}".encode()
                    sock.sendto(packet, (UDP_IP, UDP_PORT))
                    print(f"[Sent] {packet.decode()}")
                    time.sleep(0.02)
            
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n[Simulated Targets] Stopped.")

if __name__ == "__main__":
    run_simulation()
