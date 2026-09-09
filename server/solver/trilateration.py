# takes rssi from the shared_rssi conveyer belt and does trilateration to put coordinates on its own conveyer belt

"""
solver/trilateration.py
-----------------------
Pure math solver that converts active RSSI snapshot readings into a single raw (x, y) coordinate.

Pipeline Stage Contract:
- Reads: RSSI values dictionary from shared memory (shared_rssi).
- Uses: distance.py helper to calculate radiuses.
- Validates: Guarantees at least 3 active anchors exist.
- Output: Dict with {"target_id": str, "x": float, "y": float} or None if invalid.
"""

from typing import Dict, Any, Optional
import numpy as np
from scipy.optimize import least_squares
from solver.distance import rssi_to_distance


class TrilaterationSolver:

    def __init__(self, anchors: Dict[str, Dict[str, Any]], platform_ft: float):
        self.anchors = anchors
        self.platform_ft = platform_ft
        self.last_known_pos: Optional[list[float]] = None

    def solve(self, shared_rssi: Dict[str, Optional[int]], target_id: str = "T1") -> Optional[Dict[str, Any]]:
        # Filter active anchors with valid RSSI readings
        active = [(mac, cfg) for mac, cfg in self.anchors.items() if shared_rssi.get(mac) is not None]
        
        # Enforce boundary contract: Must have at least 3 active anchors for 2D trilateration
        if len(active) < 3:
            return None

        anchor_coords = []
        distances = []

        for mac, cfg in active:
            rssi = shared_rssi[mac]
            dist = rssi_to_distance(rssi, cfg["tx"], cfg["n"])
            anchor_coords.append((cfg["x"], cfg["y"]))
            distances.append(dist)

        initial_guess = self.last_known_pos if self.last_known_pos else [self.platform_ft / 2.0, self.platform_ft / 2.0]

        def residuals(pos):
            x, y = pos
            return [np.hypot(x - ax, y - ay) - d for (ax, ay), d in zip(anchor_coords, distances)]

        result = least_squares(residuals, initial_guess)
        raw_x = round(float(result.x[0]), 2)
        raw_y = round(float(result.x[1]), 2)
        
        self.last_known_pos = [raw_x, raw_y]

        # Clean output contract: Position data only
        return {
            "target_id": target_id,
            "x": raw_x,
            "y": raw_y
        }
