"""
metrics.py
----------
Computes spatial error statistics between ground truth (real) positions 
and estimated positioning coordinates.
"""

from typing import List, Dict, Any
import numpy as np


class ExperimentMetrics:

    @staticmethod
    def calculate(real_x: float, real_y: float, samples: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        :param real_x: Ground truth X coordinate (ft)
        :param real_y: Ground truth Y coordinate (ft)
        :param samples: List of dicts [{'x': float, 'y': float}, ...]
        :return: Dict containing per-sample errors and aggregate metrics
        """
        est_x = np.array([p["x"] for p in samples])
        est_y = np.array([p["y"] for p in samples])

        # Per-sample errors
        x_errors = est_x - real_x
        y_errors = est_y - real_y
        euclidean_errors = np.sqrt(x_errors**2 + y_errors**2)

        # Aggregate summary statistics
        return {
            "real_x": real_x,
            "real_y": real_y,
            "num_trials": len(samples),
            "x_error_mean": round(float(np.mean(x_errors)), 3),
            "x_error_std": round(float(np.std(x_errors)), 3),
            "y_error_mean": round(float(np.mean(y_errors)), 3),
            "y_error_std": round(float(np.std(y_errors)), 3),
            "euclidean_mean": round(float(np.mean(euclidean_errors)), 3),
            "euclidean_std": round(float(np.std(euclidean_errors)), 3),
            "rmse": round(float(np.sqrt(np.mean(euclidean_errors**2))), 3),
            "raw_samples": samples,
            "euclidean_errors": [round(float(e), 3) for e in euclidean_errors]
        }
