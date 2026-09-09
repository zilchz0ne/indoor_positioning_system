# creates T1, Anchor_MAC, simulated_RSSI and sends it to the server

import time
import socket
import random

# Target address matching receiver default
UDP_IP = "127.0.0.1"
UDP_PORT = 4210

# MAC addresses matching server/anchor_config.csv
ANCHOR_MACS = [
    "68:fe:71:8b:45:b6",  # Anchor_A (0, 0)
    "68:fe:71:8b:4c:6e",  # Anchor_B (0, 4)
    "68:fe:71:8a:f4:d2",  # Anchor_C (4, 0)
    "98:da:50:04:27:68",  # Anchor_D (4, 4)
]

TARGET_ID = "T1"

def generate_mock_rssi(base_rssi=-60, noise_level=3, outlier_chance=0.1):
    """Generates realistic RSSI readings with Gaussian noise and occasional spikes."""
    if random.random() < outlier_chance:
        # Simulate a sudden multipath/interference spike
        return random.randint(-85, -40)
    # Normal signal fluctuation
    return int(random.gauss(base_rssi, noise_level))

def run_simulation():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"[Simulated Target] Broadcasting mock BLE packets to {UDP_IP}:{UDP_PORT}...")
    
    try:
        while True:
            # Simulate target scanning and seeing all 4 anchors
            for mac in ANCHOR_MACS:
                rssi = generate_mock_rssi()
                packet = f"{TARGET_ID},{mac},{rssi}".encode()
                sock.sendto(packet, (UDP_IP, UDP_PORT))
                print(f"[Sent] {packet.decode()}")
                time.sleep(0.02)  # Short delay between anchor packet bursts
            
            time.sleep(0.2)  # Delay between full scan cycles (~5 Hz)
    except KeyboardInterrupt:
        print("\n[Simulated Target] Stopped.")

if __name__ == "__main__":
    run_simulation()
