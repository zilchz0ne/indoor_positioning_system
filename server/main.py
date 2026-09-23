"""
main.py
-------
CLI-driven experimental trial collector for Indoor Positioning System.

Usage:
    python main.py --x 2.0 --y 2.0 --samples 5
"""

import argparse
import asyncio
from collections import deque
from typing import Dict, Any, Optional, List

from config import UDP_IP, UDP_PORT, PLATFORM_FT, load_anchors
from receiver import udp_receiver
from solver.trilateration import TrilaterationSolver
from solver.dbscan_filter import DBSCANPositionFilter
from metrics import ExperimentMetrics


async def experiment_collector(
    shared_clean_positions: Dict[str, Optional[Dict[str, Any]]],
    target_samples: int,
    real_x: float,
    real_y: float,
    stop_event: asyncio.Event
):
    """Collects N unique DBSCAN-filtered samples, computes metrics, and prints formatted output."""
    collected: List[Dict[str, float]] = []
    last_seen = None

    print(f"\n[EXPERIMENT STARTED] Target real position: ({real_x:.2f}, {real_y:.2f}) ft")
    print(f"[EXPERIMENT] Collecting {target_samples} filtered samples...\n")

    while len(collected) < target_samples:
        pos = shared_clean_positions.get("T1")
        if pos and pos != last_seen:
            last_seen = pos
            collected.append({"x": pos["x"], "y": pos["y"]})
            print(f"  Sample {len(collected)}/{target_samples} -> Estimated: X={pos['x']:.2f} ft, Y={pos['y']:.2f} ft")

        await asyncio.sleep(0.1)

    # Compute metrics once required samples are collected
    results = ExperimentMetrics.calculate(real_x, real_y, collected)

    print("\n=================== EXPERIMENT SUMMARY ===================")
    print(f" Ground Truth Position : ({results['real_x']:.2f}, {results['real_y']:.2f}) ft")
    print(f" Total Trial Samples   : {results['num_trials']}")
    print(f" X-Error (Mean ± Std)  : {results['x_error_mean']:.3f} ± {results['x_error_std']:.3f} ft")
    print(f" Y-Error (Mean ± Std)  : {results['y_error_mean']:.3f} ± {results['y_error_std']:.3f} ft")
    print(f" Mean Euclidean Error  : {results['euclidean_mean']:.3f} ± {results['euclidean_std']:.3f} ft")
    print(f" Root Mean Square Error: {results['rmse']:.3f} ft")
    print("==========================================================")
    
    stop_event.set()


async def trilateration_worker(shared_rssi, shared_raw_positions, solver):
    while True:
        raw_pos = solver.solve(shared_rssi, target_id="T1")
        if raw_pos:
            shared_raw_positions.append(raw_pos)
        await asyncio.sleep(0.05)


async def dbscan_worker(shared_raw_positions, shared_clean_positions, dbscan_filter):
    while True:
        if len(shared_raw_positions) >= dbscan_filter.min_samples:
            buffer_snapshot = list(shared_raw_positions)
            clean_pos = dbscan_filter.filter_positions(buffer_snapshot)
            if clean_pos:
                shared_clean_positions["T1"] = clean_pos
        await asyncio.sleep(0.1)


async def main():
    parser = argparse.ArgumentParser(description="IPS Experimental Data Collector")
    parser.add_argument("--x", type=float, required=True, help="Real ground truth X position (ft)")
    parser.add_argument("--y", type=float, required=True, help="Real ground truth Y position (ft)")
    parser.add_argument("--samples", type=int, default=5, help="Number of estimated coordinate samples to capture (default: 5)")
    args = parser.parse_args()

    anchors = load_anchors("anchor_config.csv")

    shared_rssi: Dict[str, Optional[int]] = {mac: None for mac in anchors}
    shared_raw_positions = deque(maxlen=30)
    shared_clean_positions: Dict[str, Optional[Dict[str, Any]]] = {"T1": None}

    solver = TrilaterationSolver(anchors, PLATFORM_FT)
    dbscan_filter = DBSCANPositionFilter(eps=0.8, min_samples=4)

    stop_event = asyncio.Event()

    # Launch pipeline workers
    receiver_task = asyncio.create_task(udp_receiver(shared_rssi, UDP_IP, UDP_PORT, set(anchors.keys())))
    trilateration_task = asyncio.create_task(trilateration_worker(shared_rssi, shared_raw_positions, solver))
    dbscan_task = asyncio.create_task(dbscan_worker(shared_raw_positions, shared_clean_positions, dbscan_filter))
    collector_task = asyncio.create_task(
        experiment_collector(shared_clean_positions, args.samples, args.x, args.y, stop_event)
    )

    # Block until experiment completes
    await stop_event.wait()

    # Clean task cancellation
    receiver_task.cancel()
    trilateration_task.cancel()
    dbscan_task.cancel()
    collector_task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Experiment cancelled by user.")
