"""
test/test_trilateration.py
--------------------------
Tests the TrilaterationSolver independently using dummy anchor setups and mock RSSI inputs.
"""

from solver.trilateration import TrilaterationSolver

def test_trilateration_standalone():
    # Mock anchor config (4 ft x 4 ft box)
    mock_anchors = {
        "mac_a": {"name": "Anchor_A", "x": 0.0, "y": 0.0, "tx": -59.0, "n": 2.0},
        "mac_b": {"name": "Anchor_B", "x": 0.0, "y": 4.0, "tx": -59.0, "n": 2.0},
        "mac_c": {"name": "Anchor_C", "x": 4.0, "y": 0.0, "tx": -59.0, "n": 2.0},
        "mac_d": {"name": "Anchor_D", "x": 4.0, "y": 4.0, "tx": -59.0, "n": 2.0},
    }

    solver = TrilaterationSolver(mock_anchors, platform_ft=4.0)

    # Scenario 1: Less than 3 active anchors -> Should return None
    shared_rssi_insufficient = {"mac_a": -60, "mac_b": -65, "mac_c": None, "mac_d": None}
    res_none = solver.solve(shared_rssi_insufficient)
    print(f"[TEST 1] Insufficient anchors test: {res_none} (Expected: None)")
    assert res_none is None

    # Scenario 2: Target sitting exactly in the center (2.0, 2.0)
    # All anchors are ~2.83 ft away -> RSSI around -65 dBm
    shared_rssi_center = {"mac_a": -65, "mac_b": -65, "mac_c": -65, "mac_d": -65}
    res_center = solver.solve(shared_rssi_center)
    print(f"[TEST 2] Center target position: x={res_center['x']}, y={res_center['y']}")
    
    assert res_center is not None
    assert 1.5 <= res_center["x"] <= 2.5
    assert 1.5 <= res_center["y"] <= 2.5

    print("[SUCCESS] Trilateration solver tests passed!")

if __name__ == "__main__":
    test_trilateration_standalone()
