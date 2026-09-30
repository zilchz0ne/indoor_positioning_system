from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.cluster import HDBSCAN


class DBSCANPositionFilter:

    def __init__(self, min_cluster_size: int = 4, **kwargs):
        """
        :param min_cluster_size: Minimum neighbor points required to form a core cluster.
        """
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_cluster_size  # main.py worker check

    def filter_positions(self, raw_buffer: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not raw_buffer or len(raw_buffer) < self.min_cluster_size:
            return None

        target_id = raw_buffer[-1].get("target_id", "T1")
        coords = np.array([[pt["x"], pt["y"]] for pt in raw_buffer])

        # Run HDBSCAN clustering
        clustering = HDBSCAN(min_cluster_size=self.min_cluster_size, copy = True).fit(coords)
        labels = clustering.labels_

        # Separate valid clusters from noise (-1)
        valid_mask = labels != -1
        valid_coords = coords[valid_mask]

        # Scenario A: All points were classified as noise
        if len(valid_coords) == 0:
            mean_x, mean_y = np.mean(coords, axis=0)
            return {
                "target_id": target_id,
                "x": round(float(mean_x), 2),
                "y": round(float(mean_y), 2),
                "is_filtered": False
            }

        # Scenario B: Isolate the largest dense cluster (prevents cross-cluster averaging)
        unique_labels, counts = np.unique(labels[valid_mask], return_counts=True)
        largest_cluster = unique_labels[np.argmax(counts)]
        cluster_coords = coords[labels == largest_cluster]

        centroid_x, centroid_y = np.mean(cluster_coords, axis=0)

        return {
            "target_id": target_id,
            "x": round(float(centroid_x), 2),
            "y": round(float(centroid_y), 2),
            "is_filtered": True
        }
