"""
IPS Server — "Smart Server" in the Dumb Edge / Smart Server architecture.

Receives raw UDP from target ESPs:   TARGET_ID,ANCHOR_MAC,RSSI
Maps anchor MACs to room coordinates, converts RSSI → distance, runs trilateration.
Pushes JSON positions to the React dashboard over WebSocket.
"""

import asyncio
import json
import socket

import numpy as np
import websockets
from scipy.optimize import least_squares

# ---------------------------------------------------------------------------
# Configuration — edit anchor MACs and room layout to match your hardware
# ---------------------------------------------------------------------------
UDP_IP = "0.0.0.0"
UDP_PORT = 4210
WS_PORT = 8765

# Anchor MAC (lowercase) → name, position (meters), path-loss calibration
ANCHORS = {
    "68:fe:71:8b:45:b6": {"name": "Anchor_A", "x": 0.0, "y": 0.0, "tx": -59, "n": 2.0},
    "68:fe:71:8b:4c:6e": {"name": "Anchor_B", "x": 0.0, "y": 4.0, "tx": -59, "n": 2.0},
    "b0:cb:d8:cd:33:16": {"name": "Anchor_C", "x": 5.0, "y": 0.0, "tx": -59, "n": 2.0},
}

# Latest RSSI from each anchor (updated on every UDP packet)
latest_rssi: dict[str, int | None] = {mac: None for mac in ANCHORS}

# WebSocket clients (React dashboard)
ws_clients: set = set()

# Last computed position (used as solver starting point)
last_position: dict | None = None


# ---------------------------------------------------------------------------
# Math
# ---------------------------------------------------------------------------
def rssi_to_meters(rssi: int, tx: float, n: float) -> float:
    """Log-distance path loss: RSSI → distance in meters."""
    return 10 ** ((tx - rssi) / (10 * n))


def trilaterate() -> dict | None:
    """Return position dict if all 3 anchors have RSSI, else None."""
    if any(latest_rssi[mac] is None for mac in ANCHORS):
        return None

    anchor_xy = []
    distances = []
    rssi_out = {}
    dist_out = {}

    for mac, cfg in ANCHORS.items():
        rssi = latest_rssi[mac]
        dist = rssi_to_meters(rssi, cfg["tx"], cfg["n"])
        anchor_xy.append((cfg["x"], cfg["y"]))
        distances.append(dist)
        rssi_out[cfg["name"]] = rssi
        dist_out[cfg["name"]] = round(dist, 2)

    # Starting guess: last position, or room center
    if last_position:
        guess = [last_position["x"], last_position["y"]]
    else:
        guess = [2.5, 2.0]

    def residuals(pos, anchors=anchor_xy, measured=distances):
        x, y = pos
        return [np.hypot(x - ax, y - ay) - d for (ax, ay), d in zip(anchors, measured)]

    result = least_squares(residuals, guess)
    x, y = float(result.x[0]), float(result.x[1])

    return {
        "target_id": "T1",
        "x": round(x, 2),
        "y": round(y, 2),
        "distances": dist_out,
        "rssi": rssi_out,
    }


async def broadcast_position(pos: dict) -> None:
    """Send JSON to every connected dashboard client."""
    if not ws_clients:
        return
    msg = json.dumps(pos)
    websockets.broadcast(ws_clients, msg)


# ---------------------------------------------------------------------------
# Network handlers
# ---------------------------------------------------------------------------
async def udp_listener() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(False)
    loop = asyncio.get_running_loop()

    print(f"[UDP] Listening on port {UDP_PORT}")

    while True:
        data, addr = await loop.sock_recvfrom(sock, 1024)
        try:
            text = data.decode().strip()
            target_id, mac, rssi_str = text.split(",")
            mac = mac.lower().strip()
            rssi = int(rssi_str)

            if mac not in ANCHORS:
                print(f"[UDP] Unknown anchor {mac} from {addr[0]} — add to ANCHORS in server.py")
                continue

            latest_rssi[mac] = rssi
            print(f"[UDP] {target_id} {ANCHORS[mac]['name']} rssi={rssi}")

            global last_position
            pos = trilaterate()
            if pos:
                pos["target_id"] = target_id
                last_position = pos
                await broadcast_position(pos)
                print(f"[POS] x={pos['x']} y={pos['y']} rssi={pos['rssi']}")

        except Exception as exc:
            print(f"[UDP] Bad packet: {data!r} ({exc})")


async def ws_handler(websocket) -> None:
    ws_clients.add(websocket)
    print(f"[WS] Dashboard connected ({len(ws_clients)} client(s))")

    # Send last known position immediately on connect
    if last_position:
        await websocket.send(json.dumps(last_position))

    try:
        await websocket.wait_closed()
    finally:
        ws_clients.discard(websocket)
        print(f"[WS] Dashboard disconnected ({len(ws_clients)} client(s))")


async def main() -> None:
    async with websockets.serve(ws_handler, "0.0.0.0", WS_PORT):
        print(f"[WS]  Listening on ws://localhost:{WS_PORT}")
        await udp_listener()


if __name__ == "__main__":
    asyncio.run(main())
