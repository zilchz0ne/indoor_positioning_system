"""
main.py
-------
CLI-driven multi-target experimental trial collector and live position monitor for IPS.

Usage:
    python main.py --target T1 2.0 2.0 --target T2 1.5 3.0 --samples 5
"""

import argparse
import asyncio
from collections import deque
from typing import Dict, Any, Optional, List, Tuple

from config import UDP_IP, UDP_PORT, PLATFORM_FT, load_anchors
from receiver import udp_receiver
from solver.trilateration import TrilaterationSolver
from solver.dbscan_filter import DBSCANPositionFilter
from metrics import ExperimentMetrics


async def experiment_collector(
    shared_clean_positions: Dict[str, Optional[Dict[str, Any]]],
    target_samples: int,
    ground_truths: Dict[str, Tuple[float, float]],
    default_ground_truth: Tuple[float, float],
    stop_event: asyncio.Event
):
    """Collects N unique DBSCAN-filtered samples across discovered targets, computes metrics against per-target ground truth."""
    collected_by_target: Dict[str, List[Dict[str, float]]] = {}
    last_seen_by_target: Dict[str, Dict[str, Any]] = {}

    print("\n[EXPERIMENT STARTED]")
    print(f"[EXPERIMENT] Collecting {target_samples} filtered samples per discovered target...\n")

    while not stop_event.is_set():
        active_targets = list(shared_clean_positions.keys())

        for tid in active_targets:
            pos = shared_clean_positions.get(tid)
            if not pos:
                continue

            if tid not in collected_by_target:
                collected_by_target[tid] = []
                last_seen_by_target[tid] = {}
                gt_x, gt_y = ground_truths.get(tid, default_ground_truth)
                print(f"  [Registered Target: {tid}] Ground Truth set to ({gt_x:.2f}, {gt_y:.2f}) ft")

            if pos != last_seen_by_target[tid]:
                last_seen_by_target[tid] = pos
                collected_by_target[tid].append({"x": pos["x"], "y": pos["y"]})
                
                sample_num = len(collected_by_target[tid])
                print(f"  [Target: {tid}] Sample {sample_num}/{target_samples} -> Estimated: X={pos['x']:.2f} ft, Y={pos['y']:.2f} ft")

        if collected_by_target and all(len(samples) >= target_samples for samples in collected_by_target.values()):
            stop_event.set()
            break

        await asyncio.sleep(0.1)

    print("\n=================== EXPERIMENT SUMMARY ===================")
    print(f" Total Discovered Targets : {len(collected_by_target)}")

    for tid, samples in collected_by_target.items():
        gt_x, gt_y = ground_truths.get(tid, default_ground_truth)
        results = ExperimentMetrics.calculate(gt_x, gt_y, samples[:target_samples])
        print(f"\n --- Target ID: {tid} ---")
        print(f" Ground Truth Position : ({gt_x:.2f}, {gt_y:.2f}) ft")
        print(f" Total Trial Samples   : {results['num_trials']}")
        print(f" X-Error (Mean ± Std)  : {results['x_error_mean']:.3f} ± {results['x_error_std']:.3f} ft")
        print(f" Y-Error (Mean ± Std)  : {results['y_error_mean']:.3f} ± {results['y_error_std']:.3f} ft")
        print(f" Mean Euclidean Error  : {results['euclidean_mean']:.3f} ± {results['euclidean_std']:.3f} ft")
        print(f" Root Mean Square Error: {results['rmse']:.3f} ft")
    print("==========================================================")


async def trilateration_worker(shared_rssi, shared_raw_positions, solver):
    while True:
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
    
    # Allows passing multiple --target arguments: --target T1 2.0 2.0 --target T2 1.5 3.0
    parser.add_argument(
        "--target",
        action="append",
        nargs=3,
        metavar=("TARGET_ID", "X", "Y"),
        help="Specify target ground truth: --target TARGET_ID X Y (can be used multiple times)"
    )
    parser.add_argument("--default-x", type=float, default=2.0, help="Fallback X ground truth for unlisted discovered targets")
    parser.add_argument("--default-y", type=float, default=2.0, help="Fallback Y ground truth for unlisted discovered targets")
    parser.add_argument("--samples", type=int, default=5, help="Number of estimated coordinate samples per target (default: 5)")
    args = parser.parse_args()

    # Parse --target tuples into a dictionary: {"T1": (2.0, 2.0), "T2": (1.5, 3.0)}
    ground_truths: Dict[str, Tuple[float, float]] = {}
    if args.target:
        for tid, x_str, y_str in args.target:
            ground_truths[tid] = (float(x_str), float(y_str))

    default_gt = (args.default_x, args.default_y)

    anchors = load_anchors("anchor_config.csv")

    shared_rssi: Dict[str, Dict[str, Optional[int]]] = {}
    shared_raw_positions = deque(maxlen=60)
    shared_clean_positions: Dict[str, Optional[Dict[str, Any]]] = {}

    solver = TrilaterationSolver(anchors, PLATFORM_FT)
    dbscan_filter = DBSCANPositionFilter()

    stop_event = asyncio.Event()

    receiver_task = asyncio.create_task(udp_receiver(shared_rssi, UDP_IP, UDP_PORT, set(anchors.keys())))
    trilateration_task = asyncio.create_task(trilateration_worker(shared_rssi, shared_raw_positions, solver))
    dbscan_task = asyncio.create_task(dbscan_worker(shared_raw_positions, shared_clean_positions, dbscan_filter))
    collector_task = asyncio.create_task(
        experiment_collector(shared_clean_positions, args.samples, ground_truths, default_gt, stop_event)
    )

    await stop_event.wait()

    receiver_task.cancel()
    trilateration_task.cancel()
    dbscan_task.cancel()
    collector_task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Experiment cancelled by user.")
