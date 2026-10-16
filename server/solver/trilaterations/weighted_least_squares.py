"""
solver/trilaterations/weighted_least_squares.py
------------------------------------------------
Trilateration solver using RSSI signal-power weights.
"""

from typing import Dict, Any, Optional
import numpy as np
from scipy.optimize import least_squares
from solver.distance import rssi_to_distance


class TrilaterationSolver:

    def __init__(self, anchors: Dict[str, Dict[str, Any]], platform_ft: float, **kwargs):
        self.anchors = anchors
        self.platform_ft = platform_ft
        # Isolated state per target: { target_id: [x, y] }
        self.last_known_pos: Dict[str, list[float]] = {}

    def solve(self, shared_rssi: Dict[str, Dict[str, Optional[int]]], target_id: str = "T1") -> Optional[Dict[str, Any]]:
        target_rssi = shared_rssi.get(target_id)
        if not target_rssi:
            return None

        # Filter active anchors with valid RSSI readings for this target
        active = [(mac, cfg) for mac, cfg in self.anchors.items() if target_rssi.get(mac) is not None]

        if len(active) < 3:
            return None

        anchor_coords = []
        distances = []
        raw_rssis = []

        for mac, cfg in active:
            rssi = target_rssi[mac]
            dist = rssi_to_distance(rssi, cfg["tx"], cfg["n"])
            anchor_coords.append((cfg["x"], cfg["y"]))
            distances.append(dist)
            raw_rssis.append(rssi)

        raw_weights = [10.0 ** (rssi / 10.0) for rssi in raw_rssis]
        max_w = max(raw_weights) if raw_weights else 1.0
        weights = [w / max_w for w in raw_weights]

        initial_guess = (
            self.last_known_pos[target_id]
            if target_id in self.last_known_pos
            else [self.platform_ft / 2.0, self.platform_ft / 2.0]
        )

        def weighted_residuals(pos):
            x, y = pos
            return [
                w * (np.hypot(x - ax, y - ay) - d)
                for (ax, ay), d, w in zip(anchor_coords, distances, weights)
            ]

        result = least_squares(weighted_residuals, initial_guess)
        raw_x = round(float(result.x[0]), 2)
        raw_y = round(float(result.x[1]), 2)

        self.last_known_pos[target_id] = [raw_x, raw_y]

        return {
            "target_id": target_id,
            "x": raw_x,
            "y": raw_y
        }
