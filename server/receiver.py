"""
receiver.py
-----------
Listens continuously for UDP packets broadcasted by Target nodes over the local network.
"""

import asyncio
import socket
from typing import Dict, Optional


async def udp_receiver(
    shared_rssi: Dict[str, Dict[str, Optional[int]]], 
    ip: str, 
    port: int, 
    valid_macs: set
) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))
    sock.setblocking(False)
    loop = asyncio.get_running_loop()

    print(f"[Receiver] Listening on UDP {port}")
    while True:
        data, addr = await loop.sock_recvfrom(sock, 1024)
        try:
            text = data.decode().strip()
            parts = text.split(",")
            if len(parts) != 3:
                continue

            target_id, mac, rssi_str = parts
            target_id = target_id.strip()
            mac = mac.lower().strip()

            if not target_id:
                continue

            if mac in valid_macs:
                if target_id not in shared_rssi:
                    shared_rssi[target_id] = {}
                shared_rssi[target_id][mac] = int(rssi_str)
            else:
                print(f"[Receiver] Unknown anchor {mac} from {addr[0]}")

        except Exception as exc:
            print(f"[Receiver] Bad packet: {data!r} ({exc})")
