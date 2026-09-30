from typing import Dict, Any, Optional
import numpy as np
from scipy.optimize import least_squares
from solver.distance import rssi_to_distance


class TrilaterationSolver:

    def __init__(self, anchors: Dict[str, Dict[str, Any]], platform_ft: float, **kwargs):
        """
        :param anchors: Dictionary of anchor configurations with MACs as keys.
        :param platform_ft: Room/Platform dimension bound in feet.
        """
        self.anchors = anchors
        self.platform_ft = platform_ft
        self.last_known_pos: Optional[list[float]] = None

    def solve(self, shared_rssi: Dict[str, Optional[int]], target_id: str = "T1") -> Optional[Dict[str, Any]]:
        # Filter active anchors with valid RSSI readings
        active = [(mac, cfg) for mac, cfg in self.anchors.items() if shared_rssi.get(mac) is not None]

        # Enforce boundary contract: Must have at least 3 active anchors
        if len(active) < 3:
            return None

        anchor_coords = []
        distances = []
        raw_rssis = []

        for mac, cfg in active:
            rssi = shared_rssi[mac]
            dist = rssi_to_distance(rssi, cfg["tx"], cfg["n"])
            anchor_coords.append((cfg["x"], cfg["y"]))
            distances.append(dist)
            raw_rssis.append(rssi)

        # Calculate linear power weights: w = 10^(RSSI / 10)
        # Normalize relative to max weight in current snapshot for numerical stability
        raw_weights = [10.0 ** (rssi / 10.0) for rssi in raw_rssis]
        max_w = max(raw_weights) if raw_weights else 1.0
        weights = [w / max_w for w in raw_weights]

        initial_guess = (
            self.last_known_pos
            if self.last_known_pos
            else [self.platform_ft / 2.0, self.platform_ft / 2.0]
        )

        # Weighted residuals function: residuals multiplied by normalized weights
        def weighted_residuals(pos):
            x, y = pos
            return [
                w * (np.hypot(x - ax, y - ay) - d)
                for (ax, ay), d, w in zip(anchor_coords, distances, weights)
            ]

        result = least_squares(weighted_residuals, initial_guess)
        raw_x = round(float(result.x[0]), 2)
        raw_y = round(float(result.x[1]), 2)

        self.last_known_pos = [raw_x, raw_y]

        return {
            "target_id": target_id,
            "x": raw_x,
            "y": raw_y
        }
