"""
solver/trilaterations/vanilla_least_squares.py
-----------------------------------------------
Pure math solver that converts active RSSI snapshot readings into a single raw (x, y) coordinate.
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

        # Enforce boundary contract: Must have at least 3 active anchors
        if len(active) < 3:
            return None

        anchor_coords = []
        distances = []

        for mac, cfg in active:
            rssi = target_rssi[mac]
            dist = rssi_to_distance(rssi, cfg["tx"], cfg["n"])
            anchor_coords.append((cfg["x"], cfg["y"]))
            distances.append(dist)

        initial_guess = (
            self.last_known_pos[target_id]
            if target_id in self.last_known_pos
            else [self.platform_ft / 2.0, self.platform_ft / 2.0]
        )

        def residuals(pos):
            x, y = pos
            return [np.hypot(x - ax, y - ay) - d for (ax, ay), d in zip(anchor_coords, distances)]

        result = least_squares(residuals, initial_guess)
        raw_x = round(float(result.x[0]), 2)
        raw_y = round(float(result.x[1]), 2)

        self.last_known_pos[target_id] = [raw_x, raw_y]

        return {
            "target_id": target_id,
            "x": raw_x,
            "y": raw_y
        }
