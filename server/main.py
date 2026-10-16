"""
main.py
-------
CLI-driven multi-target experimental trial collector and live position monitor for IPS.

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
    """Collects N unique DBSCAN-filtered samples across discovered targets, computes metrics, and prints output."""
    collected_by_target: Dict[str, List[Dict[str, float]]] = {}
    last_seen_by_target: Dict[str, Dict[str, Any]] = {}

    print(f"\n[EXPERIMENT STARTED] Ground truth position: ({real_x:.2f}, {real_y:.2f}) ft")
    print(f"[EXPERIMENT] Collecting {target_samples} filtered samples per discovered target...\n")

    while not stop_event.is_set():
        # Snapshot active targets from shared state
        active_targets = list(shared_clean_positions.keys())

        for tid in active_targets:
            pos = shared_clean_positions.get(tid)
            if not pos:
                continue

            # Initialize target tracking buffers dynamically
            if tid not in collected_by_target:
                collected_by_target[tid] = []
                last_seen_by_target[tid] = {}

            if pos != last_seen_by_target[tid]:
                last_seen_by_target[tid] = pos
                collected_by_target[tid].append({"x": pos["x"], "y": pos["y"]})
                
                sample_num = len(collected_by_target[tid])
                print(f"  [Target: {tid}] Sample {sample_num}/{target_samples} -> Estimated: X={pos['x']:.2f} ft, Y={pos['y']:.2f} ft")

        # Check if all currently discovered targets have reached the sample count requirement
        if collected_by_target and all(len(samples) >= target_samples for samples in collected_by_target.values()):
            stop_event.set()
            break

        await asyncio.sleep(0.1)

    print("\n=================== EXPERIMENT SUMMARY ===================")
    print(f" Ground Truth Position : ({real_x:.2f}, {real_y:.2f}) ft")
    print(f" Total Discovered Targets : {len(collected_by_target)}")

    for tid, samples in collected_by_target.items():
        results = ExperimentMetrics.calculate(real_x, real_y, samples[:target_samples])
        print(f"\n --- Target ID: {tid} ---")
        print(f" Total Trial Samples   : {results['num_trials']}")
        print(f" X-Error (Mean ± Std)  : {results['x_error_mean']:.3f} ± {results['x_error_std']:.3f} ft")
        print(f" Y-Error (Mean ± Std)  : {results['y_error_mean']:.3f} ± {results['y_error_std']:.3f} ft")
        print(f" Mean Euclidean Error  : {results['euclidean_mean']:.3f} ± {results['euclidean_std']:.3f} ft")
        print(f" Root Mean Square Error: {results['rmse']:.3f} ft")
    print("==========================================================")


async def trilateration_worker(shared_rssi, shared_raw_positions, solver):
    while True:
        # Dynamically solve for all targets active in shared_rssi
        target_ids = list(shared_rssi.keys())
        for tid in target_ids:
            raw_pos = solver.solve(shared_rssi, target_id=tid)
            if raw_pos:
                shared_raw_positions.append(raw_pos)
        await asyncio.sleep(0.05)


async def dbscan_worker(shared_raw_positions, shared_clean_positions, dbscan_filter):
    while True:
        if len(shared_raw_positions) >= dbscan_filter.min_samples:
            buffer_snapshot = list(shared_raw_positions)

            # Partition buffer readings by target_id
            by_target: Dict[str, List[Dict[str, Any]]] = {}
            for pt in buffer_snapshot:
                tid = pt.get("target_id")
                if tid:
                    by_target.setdefault(tid, []).append(pt)

            for tid, target_pts in by_target.items():
                if len(target_pts) >= dbscan_filter.min_samples:
                    clean_pos = dbscan_filter.filter_positions(target_pts)
                    if clean_pos:
                        shared_clean_positions[tid] = clean_pos

        await asyncio.sleep(0.1)


async def main():
    parser = argparse.ArgumentParser(description="IPS Multi-Target Experimental Data Collector")
    parser.add_argument("--x", type=float, required=True, help="Real ground truth X position (ft)")
    parser.add_argument("--y", type=float, required=True, help="Real ground truth Y position (ft)")
    parser.add_argument("--samples", type=int, default=5, help="Number of estimated coordinate samples to capture per target (default: 5)")
    args = parser.parse_args()

    anchors = load_anchors("anchor_config.csv")

    # 2D mapping initialized empty: { target_id: { mac: rssi } }
    shared_rssi: Dict[str, Dict[str, Optional[int]]] = {}
    shared_raw_positions = deque(maxlen=60)  # Expanded buffer to hold multi-target snapshots
    shared_clean_positions: Dict[str, Optional[Dict[str, Any]]] = {}

    solver = TrilaterationSolver(anchors, PLATFORM_FT)
    dbscan_filter = DBSCANPositionFilter()

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
