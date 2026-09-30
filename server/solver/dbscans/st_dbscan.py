from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.cluster import DBSCAN


class DBSCANPositionFilter:


    def __init__(self, eps_spatial: float = 0.8, eps_temporal: float = 5.0, min_samples: int = 4, **kwargs):
        """
        :param eps_spatial: Spatial neighborhood distance threshold (ft).
        :param eps_temporal: Maximum index difference allowed between buffer samples.
        :param min_samples: Minimum neighbor points required to form a cluster.
        """
        self.eps_spatial = eps_spatial
        self.eps_temporal = eps_temporal
        self.min_samples = min_samples

    def filter_positions(self, raw_buffer: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not raw_buffer or len(raw_buffer) < self.min_samples:
            return None

        target_id = raw_buffer[-1].get("target_id", "T1")

        # Convert buffer points into 3D features: [X, Y, TimeIndex]
        # Index acts as a relative time step (0, 1, 2, ..., N)
        coords_3d = np.array([[pt["x"], pt["y"], i] for i, pt in enumerate(raw_buffer)])
        coords_2d = coords_3d[:, :2]

        # 1. First-pass DBSCAN on 2D Spatial Distance
        spatial_db = DBSCAN(eps=self.eps_spatial, min_samples=self.min_samples).fit(coords_2d)
        labels = spatial_db.labels_

        # 2. Refine clusters by filtering out temporal disconnects within spatial clusters
        final_labels = np.full(labels.shape, -1)

        for label in set(labels):
            if label == -1:
                continue

            indices = np.where(labels == label)[0]
            # Check if points in cluster are contiguous/close enough in time
            time_diffs = np.diff(indices)

            # If points are too far apart in sequence index, reject as temporal noise
            if np.all(time_diffs <= self.eps_temporal):
                final_labels[indices] = label

        valid_mask = final_labels != -1
        valid_coords = coords_2d[valid_mask]

        # Scenario A: All points failed spatio-temporal validation
        if len(valid_coords) == 0:
            mean_x, mean_y = np.mean(coords_2d, axis=0)
            return {
                "target_id": target_id,
                "x": round(float(mean_x), 2),
                "y": round(float(mean_y), 2),
                "is_filtered": False
            }

        # Scenario B: Extract largest spatio-temporal cluster
        unique_labels, counts = np.unique(final_labels[valid_mask], return_counts=True)
        largest_cluster = unique_labels[np.argmax(counts)]
        cluster_coords = coords_2d[final_labels == largest_cluster]

        centroid_x, centroid_y = np.mean(cluster_coords, axis=0)

        return {
            "target_id": target_id,
            "x": round(float(centroid_x), 2),
            "y": round(float(centroid_y), 2),
            "is_filtered": True
        }
