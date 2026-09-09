import asyncio
from config import UDP_IP, UDP_PORT, load_anchors
from receiver import udp_receiver

async def test_receiver_standalone():
    anchors = load_anchors("anchor_config.csv")
    shared_rssi = {mac: None for mac in anchors}
    
    print("[TEST] Starting udp_receiver... Waiting for mock UDP packets.")
    
    # Task to monitor shared memory updates in real time
    async def monitor_memory():
        while True:
            await asyncio.sleep(1)
            print(f"[TEST SHARED MEMORY STATE] {shared_rssi}")

    await asyncio.gather(
        udp_receiver(shared_rssi, UDP_IP, UDP_PORT, set(anchors.keys())),
        monitor_memory()
    )

if __name__ == "__main__":
    asyncio.run(test_receiver_standalone())
