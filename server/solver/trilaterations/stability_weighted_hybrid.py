from typing import Dict, Any, Optional
from collections import deque
import numpy as np
from scipy.optimize import least_squares
from solver.distance import rssi_to_distance


class TrilaterationSolver:

    def __init__(self, anchors: Dict[str, Dict[str, Any]], platform_ft: float, buffer_size: int = 10, **kwargs):
        """
        :param anchors: Dictionary of anchor configurations with MACs as keys.
        :param platform_ft: Room/Platform dimension bound in feet.
        :param buffer_size: Number of recent RSSI samples per anchor to store for variance computation.
        """
        self.anchors = anchors
        self.platform_ft = platform_ft
        self.buffer_size = buffer_size
        self.last_known_pos: Optional[list[float]] = None

        # Internal buffer: MAC -> deque of recent RSSI readings
        self.rssi_buffers: Dict[str, deque] = {mac: deque(maxlen=buffer_size) for mac in anchors}

    def solve(self, shared_rssi: Dict[str, Optional[int]], target_id: str = "T1") -> Optional[Dict[str, Any]]:
        # Update internal buffers for all anchors that sent a valid RSSI reading
        for mac in self.anchors:
            rssi = shared_rssi.get(mac)
            if rssi is not None:
                self.rssi_buffers[mac].append(rssi)

        # Filter active anchors with valid RSSI readings
        active = [(mac, cfg) for mac, cfg in self.anchors.items() if shared_rssi.get(mac) is not None]

        # Enforce boundary contract: Must have at least 3 active anchors
        if len(active) < 3:
            return None

        anchor_coords = []
        distances = []
        raw_weights = []

        epsilon = 1e-3  # Small constant to prevent division by zero when variance is 0

        for mac, cfg in active:
            rssi = shared_rssi[mac]
            dist = rssi_to_distance(rssi, cfg["tx"], cfg["n"])
            anchor_coords.append((cfg["x"], cfg["y"]))
            distances.append(dist)

            # 1. Power component: 10^(RSSI / 10)
            power_w = 10.0 ** (rssi / 10.0)

            # 2. Variance component: 1 / (var + eps)
            buf = self.rssi_buffers[mac]
            if len(buf) >= 3:
                var = float(np.var(buf))
            else:
                var = 0.0  # Warm-up phase: treat variance as zero until buffer populates

            inv_var_w = 1.0 / (var + epsilon)

            # 3. Hybrid Weight
            raw_weights.append(power_w * inv_var_w)

        # Normalize weights relative to max weight in snapshot for numerical stability
        max_w = max(raw_weights) if raw_weights else 1.0
        weights = [w / max_w for w in raw_weights]

        initial_guess = (
            self.last_known_pos
            if self.last_known_pos
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

        self.last_known_pos = [raw_x, raw_y]

        return {
            "target_id": target_id,
            "x": raw_x,
            "y": raw_y
        }
