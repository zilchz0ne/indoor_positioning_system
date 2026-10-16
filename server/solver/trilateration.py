from typing import Dict, Any, Optional
from collections import deque
import numpy as np
from scipy.optimize import least_squares
from solver.distance import rssi_to_distance


class TrilaterationSolver:

    def __init__(self, anchors: Dict[str, Dict[str, Any]], platform_ft: float, buffer_size: int = 10, **kwargs):
        self.anchors = anchors
        self.platform_ft = platform_ft
        self.buffer_size = buffer_size
        
        # Track state per target: { target_id: [x, y] }
        self.last_known_pos: Dict[str, list[float]] = {}
        # Track buffers per target: { target_id: { mac: deque(...) } }
        self.rssi_buffers: Dict[str, Dict[str, deque]] = {}

    def solve(self, shared_rssi: Dict[str, Dict[str, Optional[int]]], target_id: str = "T1") -> Optional[Dict[str, Any]]:
        target_rssi = shared_rssi.get(target_id)
        if not target_rssi:
            return None

        # Initialize buffers for new target
        if target_id not in self.rssi_buffers:
            self.rssi_buffers[target_id] = {mac: deque(maxlen=self.buffer_size) for mac in self.anchors}

        # Update internal buffers for active readings
        for mac in self.anchors:
            rssi = target_rssi.get(mac)
            if rssi is not None:
                self.rssi_buffers[target_id][mac].append(rssi)

        # Filter active anchors with valid RSSI readings for this target
        active = [(mac, cfg) for mac, cfg in self.anchors.items() if target_rssi.get(mac) is not None]

        if len(active) < 3:
            return None

        anchor_coords = []
        distances = []
        raw_weights = []
        epsilon = 1e-3

        for mac, cfg in active:
            rssi = target_rssi[mac]
            dist = rssi_to_distance(rssi, cfg["tx"], cfg["n"])
            anchor_coords.append((cfg["x"], cfg["y"]))
            distances.append(dist)

            power_w = 10.0 ** (rssi / 10.0)

            buf = self.rssi_buffers[target_id][mac]
            var = float(np.var(buf)) if len(buf) >= 3 else 0.0

            inv_var_w = 1.0 / (var + epsilon)
            raw_weights.append(power_w * inv_var_w)

        max_w = max(raw_weights) if raw_weights else 1.0
        weights = [w / max_w for w in raw_weights]

        initial_guess = (
            self.last_known_pos[target_id]
            if target_id in self.last_known_pos
            else [self.platform_ft / 2.0, self.platform_ft / 2.0]
        )

        def hybrid_weighted_residuals(pos):
            x, y = pos
            return [
                w * (np.hypot(x - ax, y - ay) - d)
                for (ax, ay), d, w in zip(anchor_coords, distances, weights)
            ]

        result = least_squares(hybrid_weighted_residuals, initial_guess)
        raw_x = round(float(result.x[0]), 2)
        raw_y = round(float(result.x[1]), 2)

        self.last_known_pos[target_id] = [raw_x, raw_y]

        return {
            "target_id": target_id,
            "x": raw_x,
            "y": raw_y
        }
