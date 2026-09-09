"""
test/test_dbscan_filter.py
---------------------------
Tests DBSCANPositionFilter standalone with synthetic raw position buffers.
"""

from solver.dbscan_filter import DBSCANPositionFilter

def test_dbscan_filter_standalone():
    dbscan_filter = DBSCANPositionFilter(eps=1.0, min_samples=4)

    # 1. Generate 10 dense cluster points around (2.0, 2.0)
    normal_points = [
        {"target_id": "T1", "x": 2.0, "y": 2.1},
        {"target_id": "T1", "x": 2.1, "y": 2.0},
        {"target_id": "T1", "x": 1.9, "y": 1.9},
        {"target_id": "T1", "x": 2.0, "y": 1.95},
        {"target_id": "T1", "x": 2.05, "y": 2.05},
        {"target_id": "T1", "x": 1.95, "y": 2.0},
        {"target_id": "T1", "x": 2.0, "y": 2.0},
        {"target_id": "T1", "x": 2.1, "y": 2.1},
        {"target_id": "T1", "x": 1.9, "y": 2.05},
        {"target_id": "T1", "x": 2.02, "y": 1.98},
    ]

    # 2. Add 3 wild noise outlier points caused by multipath signal drops
    outliers = [
        {"target_id": "T1", "x": 12.0, "y": -5.0},
        {"target_id": "T1", "x": -8.0, "y": 14.0},
        {"target_id": "T1", "x": 15.0, "y": 15.0},
    ]

    buffer = normal_points + outliers

    # Filter the buffer
    result = dbscan_filter.filter_positions(buffer)

    print("\n--- DBSCAN Filter Test Result ---")
    print(f"Input Buffer Size: {len(buffer)} points (10 valid, 3 noise outliers)")
    print(f"Filtered Result:   {result}")

    # Assertions
    assert result is not None
    assert result["is_filtered"] is True
    # Clean centroid should remain near (2.0, 2.0), ignoring the wild outliers
    assert 1.8 <= result["x"] <= 2.2
    assert 1.8 <= result["y"] <= 2.2

    print("[SUCCESS] DBSCAN filter successfully stripped spatial outliers!\n")

if __name__ == "__main__":
    test_dbscan_filter_standalone()
