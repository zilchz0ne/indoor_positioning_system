"""
IPS Server — "Smart Server" in the Dumb Edge / Smart Server architecture.

Receives raw UDP from target ESPs:   TARGET_ID,ANCHOR_MAC,RSSI
Maps anchor MACs to room coordinates, converts RSSI → distance, runs trilateration.
Pushes JSON positions to the React dashboard over WebSocket.
"""

import asyncio
import csv
import json
import socket
from pathlib import Path

import numpy as np
import websockets
from scipy.optimize import least_squares

# ---------------------------------------------------------------------------
# Server Constants
# ---------------------------------------------------------------------------
UDP_IP = "0.0.0.0"
UDP_PORT = 4210
WS_PORT = 8765
PLATFORM_FT = 4.0


# ---------------------------------------------------------------------------
# Anchor Loader
# ---------------------------------------------------------------------------
def load_anchors_from_csv(file_path: str = "anchor_config.csv") -> dict[str, dict]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Anchor configuration file '{file_path}' not found.")

    anchors = {}
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mac = row["mac"].strip().lower()
            anchors[mac] = {
                "name": row["name"].strip(),
                "x": float(row["x"]),
                "y": float(row["y"]),
                "tx": float(row["tx"]),
                "n": float(row["n"]),
            }
    return anchors


ANCHORS = load_anchors_from_csv()

latest_rssi: dict[str, int | None] = {mac: None for mac in ANCHORS}
ws_clients: set = set()
last_position: dict | None = None


# ---------------------------------------------------------------------------
# Core Math
# ---------------------------------------------------------------------------
def rssi_to_distance(rssi: int, tx: float, n: float) -> float:
    return 10 ** ((tx - rssi) / (10 * n))


def trilaterate() -> dict | None:
    active = [(mac, cfg) for mac, cfg in ANCHORS.items() if latest_rssi.get(mac) is not None]
    if len(active) < 3:
        return None

    anchor_xy, distances, rssi_out, dist_out = [], [], {}, {}

    for mac, cfg in active:
        rssi = latest_rssi[mac]
        dist = rssi_to_distance(rssi, cfg["tx"], cfg["n"])
        anchor_xy.append((cfg["x"], cfg["y"]))
        distances.append(dist)
        rssi_out[cfg["name"]] = rssi
        dist_out[cfg["name"]] = round(dist, 2)

    guess = [last_position["x"], last_position["y"]] if last_position else [PLATFORM_FT / 2, PLATFORM_FT / 2]

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


# ---------------------------------------------------------------------------
# Network Handlers
# ---------------------------------------------------------------------------
async def broadcast_position(pos: dict) -> None:
    if ws_clients:
        websockets.broadcast(ws_clients, json.dumps(pos))


def anchor_config_message() -> str:
    anchors = [{"name": cfg["name"], "x": cfg["x"], "y": cfg["y"]} for cfg in ANCHORS.values()]
    room_w = max((a["x"] for a in anchors), default=PLATFORM_FT)
    room_h = max((a["y"] for a in anchors), default=PLATFORM_FT)
    return json.dumps({
        "type": "config",
        "anchors": anchors,
        "room": {
            "width": room_w,
            "height": room_h,
            "unit": "ft",
            "label": f"{PLATFORM_FT:.0f} ft × {PLATFORM_FT:.0f} ft",
        },
    })


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
                print(f"[UDP] Unknown anchor {mac} from {addr[0]}")
                continue

            latest_rssi[mac] = rssi

            global last_position
            pos = trilaterate()
            if pos:
                pos["target_id"] = target_id
                last_position = pos
                await broadcast_position(pos)
                print(f"[POS] x={pos['x']} y={pos['y']}")

        except Exception as exc:
            print(f"[UDP] Bad packet: {data!r} ({exc})")


async def ws_handler(websocket) -> None:
    ws_clients.add(websocket)
    print(f"[WS] Client connected ({len(ws_clients)})")
    await websocket.send(anchor_config_message())
    if last_position:
        await websocket.send(json.dumps(last_position))

    try:
        await websocket.wait_closed()
    finally:
        ws_clients.discard(websocket)


async def main() -> None:
    async with websockets.serve(ws_handler, "0.0.0.0", WS_PORT):
        print(f"[WS] Listening on ws://0.0.0.0:{WS_PORT}")
        await udp_listener()


if __name__ == "__main__":
    asyncio.run(main())
