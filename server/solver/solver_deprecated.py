import numpy as np
from scipy.optimize import least_squares


class TrilaterationSolver:

    def __init__(self, anchors: dict[str, dict], platform_ft: float):
        self.anchors = anchors
        self.platform_ft = platform_ft
        self.last_position: dict | None = None

    def rssi_to_distance(self, rssi: int, tx: float, n: float) -> float:
        return 10 ** ((tx - rssi) / (10 * n))

    def solve(self, shared_rssi: dict[str, int | None], target_id: str = "T1") -> dict | None:
        # Read snapshot of active anchors from shared memory
        active = [(mac, cfg) for mac, cfg in self.anchors.items() if shared_rssi.get(mac) is not None]
        if len(active) < 3:
            return None

        anchor_xy, distances, rssi_out, dist_out = [], [], {}, {}

        for mac, cfg in active:
            rssi = shared_rssi[mac]
            dist = self.rssi_to_distance(rssi, cfg["tx"], cfg["n"])
            anchor_xy.append((cfg["x"], cfg["y"]))
            distances.append(dist)
            rssi_out[cfg["name"]] = rssi
            dist_out[cfg["name"]] = round(dist, 2)

        guess = (
            [self.last_position["x"], self.last_position["y"]]
            if self.last_position
            else [self.platform_ft / 2, self.platform_ft / 2]
        )

        def residuals(pos):
            x, y = pos
            return [np.hypot(x - ax, y - ay) - d for (ax, ay), d in zip(anchor_xy, distances)]

        result = least_squares(residuals, guess)
        pos = {
            "target_id": target_id,
            "x": round(float(result.x[0]), 2),
            "y": round(float(result.x[1]), 2),
            "distances": dist_out,
            "rssi": rssi_out,
        }
        self.last_position = pos
        return pos
