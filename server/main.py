import asyncio
import websockets
from broadcaster import WebSocketBroadcaster
from config import UDP_IP, UDP_PORT, WS_PORT, PLATFORM_FT, load_anchors
from receiver import udp_receiver
from solver import TrilaterationSolver


async def processing_loop(shared_rssi: dict, solver: TrilaterationSolver, broadcaster: WebSocketBroadcaster):
    """Periodically evaluates shared memory state and broadcasts position updates."""
    while True:
        pos = solver.solve(shared_rssi)
        if pos:
            await broadcaster.broadcast(pos)
            print(f"[POS] x={pos['x']} y={pos['y']}")
        
        # Run solver tick (e.g., 20 Hz = 50ms interval)
        await asyncio.sleep(0.05)


async def main():
    anchors = load_anchors("anchor_config.csv")

    # Shared RAM register for latest RSSI readings per anchor
    shared_rssi: dict[str, int | None] = {mac: None for mac in anchors}

    solver = TrilaterationSolver(anchors, PLATFORM_FT)
    broadcaster = WebSocketBroadcaster(anchors, PLATFORM_FT)

    async def ws_wrapper(websocket):
        await broadcaster.handler(websocket, solver.last_position)

    async with websockets.serve(ws_wrapper, "0.0.0.0", WS_PORT):
        print(f"[WS] Listening on ws://0.0.0.0:{WS_PORT}")
        await asyncio.gather(
            udp_receiver(shared_rssi, UDP_IP, UDP_PORT, set(anchors.keys())),
            processing_loop(shared_rssi, solver, broadcaster),
        )


if __name__ == "__main__":
    asyncio.run(main())
