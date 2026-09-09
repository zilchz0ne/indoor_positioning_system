from solver.distance import rssi_to_distance

def test_distance_calculation():
    tx_power = -59.0
    n = 2.0

    # Case 1: RSSI matches TxPower -> Distance should be 1.0 ft
    d1 = rssi_to_distance(-59, tx_power, n)
    print(f"[TEST] RSSI=-59 -> Distance={d1:.2f} ft (Expected: ~1.00)")
    assert round(d1, 2) == 1.00

    # Case 2: Weaker RSSI (-65 dBm) -> Distance should grow
    d2 = rssi_to_distance(-65, tx_power, n)
    print(f"[TEST] RSSI=-65 -> Distance={d2:.2f} ft (Expected: > 1.00)")
    assert d2 > 1.00

    print("[SUCCESS] distance.py tests passed!")

if __name__ == "__main__":
    test_distance_calculation()
