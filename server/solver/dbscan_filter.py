# dbscan which filters out outliers ig

"""
solver/dbscan_filter.py
-----------------------
Density-based spatial noise filter for indoor positioning coordinates.

Pipeline Stage Contract:
- Input: Takes a list/buffer of raw (x, y) coordinate dicts from upstream trilateration.
- Algorithm: Runs DBSCAN on spatial 2D points.
- Filtering: Identifies dense clusters, drops spatial noise (-1), and computes cluster centroid.
- Output: Dict {"target_id": str, "x": float, "y": float, "is_filtered": bool} or None.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.cluster import DBSCAN


class DBSCANPositionFilter:

    def __init__(self, eps: float = 0.8, min_samples: int = 4):
        """
        :param eps: Maximum neighborhood distance in feet (e.g., 0.8 ft radius).
        :param min_samples: Minimum neighbor points required to form a core cluster.
        """
        self.eps = eps
        self.min_samples = min_samples

    def filter_positions(self, raw_buffer: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not raw_buffer or len(raw_buffer) < self.min_samples:
            # Not enough sample points in buffer to run density clustering yet
            return None

        target_id = raw_buffer[-1].get("target_id", "T1")

        # Extract 2D coordinate array [[x1, y1], [x2, y2], ...]
        coords = np.array([[pt["x"], pt["y"]] for pt in raw_buffer])

        # Run DBSCAN clustering
        clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(coords)
        labels = clustering.labels_

        # Separate cluster points from noise points (-1)
        valid_mask = labels != -1
        valid_coords = coords[valid_mask]

        # Scenario A: All points were classified as noise
        if len(valid_coords) == 0:
            # Fallback to simple average of recent points if no dense cluster formed
            mean_x, mean_y = np.mean(coords, axis=0)
            return {"target_id": target_id, "x": round(float(mean_x), 2), "y": round(float(mean_y), 2), "is_filtered": False}

        # Scenario B: Dense cluster found! Calculate centroid of non-noise points
        centroid_x, centroid_y = np.mean(valid_coords, axis=0)

        return {
            "target_id": target_id,
            "x": round(float(centroid_x), 2),
            "y": round(float(centroid_y), 2),
            "is_filtered": True
        }
