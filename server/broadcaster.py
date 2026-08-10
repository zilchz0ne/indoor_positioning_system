import json
import websockets


class WebSocketBroadcaster:

    def __init__(self, anchors: dict[str, dict], platform_ft: float):
        self.clients = set()
        self.anchors = anchors
        self.platform_ft = platform_ft

    def get_config_message(self) -> str:
        anchors_list = [{"name": cfg["name"], "x": cfg["x"], "y": cfg["y"]} for cfg in self.anchors.values()]
        return json.dumps({
            "type": "config",
            "anchors": anchors_list,
            "room": {
                "width": self.platform_ft,
                "height": self.platform_ft,
                "unit": "ft",
                "label": f"{self.platform_ft:.0f} ft × {self.platform_ft:.0f} ft",
            },
        })

    async def handler(self, websocket, last_position: dict | None):
        self.clients.add(websocket)
        print(f"[WS] Client connected ({len(self.clients)})")
        await websocket.send(self.get_config_message())

        if last_position:
            await websocket.send(json.dumps(last_position))

        try:
            await websocket.wait_closed()
        finally:
            self.clients.discard(websocket)
            print(f"[WS] Client disconnected ({len(self.clients)})")

    async def broadcast(self, position_data: dict) -> None:
        if self.clients:
            websockets.broadcast(self.clients, json.dumps(position_data))
