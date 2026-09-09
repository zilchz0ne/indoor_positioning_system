"""
main.py
-------
Main entry point for the Indoor Positioning System server.

Orchestrates all pipeline stages using shared conveyor belts:
1. receiver.py          -> Ingests UDP packets -> shared_rssi
2. trilateration_worker -> Computes raw (x,y)   -> shared_raw_positions
3. dbscan_worker        -> Filters noise (x,y) -> shared_clean_positions
4. display.py           -> Prints to Terminal  <- shared_clean_positions
"""

import asyncio
from collections import deque
from typing import Dict, Any, Optional

from config import UDP_IP, UDP_PORT, PLATFORM_FT, load_anchors
from receiver import udp_receiver
from solver.trilateration import TrilaterationSolver
from solver.dbscan_filter import DBSCANPositionFilter
from display import terminal_display_worker


async def trilateration_worker(
    shared_rssi: Dict[str, Optional[int]],
    shared_raw_positions: deque,
    solver: TrilaterationSolver
):
    """Pipeline Stage 2: Periodically computes raw (x, y) coordinates from RSSI."""
    while True:
        raw_pos = solver.solve(shared_rssi, target_id="T1")
        if raw_pos:
            shared_raw_positions.append(raw_pos)
        await asyncio.sleep(0.05)  # Run at 20 Hz (50 ms)


async def dbscan_worker(
    shared_raw_positions: deque,
    shared_clean_positions: Dict[str, Optional[Dict[str, Any]]],
    dbscan_filter: DBSCANPositionFilter
):
    """Pipeline Stage 3: Periodically runs DBSCAN on the raw positions buffer."""
    while True:
        if len(shared_raw_positions) >= dbscan_filter.min_samples:
            # Create a snapshot slice of the current position buffer
            buffer_snapshot = list(shared_raw_positions)
            clean_pos = dbscan_filter.filter_positions(buffer_snapshot)
            if clean_pos:
                shared_clean_positions["T1"] = clean_pos

        await asyncio.sleep(0.1)  # Run filtering at 10 Hz (100 ms)


async def main():
    # Load anchor configuration from CSV
    anchors = load_anchors("anchor_config.csv")

    # ==========================================
    # CONVEYOR BELTS (SHARED IN-MEMORY REGISTERS)
    # ==========================================
    # Conveyor Belt 1: Raw RSSI state per anchor MAC
    shared_rssi: Dict[str, Optional[int]] = {mac: None for mac in anchors}

    # Conveyor Belt 2: Sliding buffer of recent raw (x, y) positions (max 30 items)
    shared_raw_positions = deque(maxlen=30)

    # Conveyor Belt 3: Single clean, DBSCAN-filtered target position
    shared_clean_positions: Dict[str, Optional[Dict[str, Any]]] = {"T1": None}

    # ==========================================
    # PIPELINE WORKERS & SERVICES
    # ==========================================
    solver = TrilaterationSolver(anchors, PLATFORM_FT)
    dbscan_filter = DBSCANPositionFilter(eps=0.8, min_samples=4)

    print("[SERVER START] Launching asynchronous processing tasks...")

    # Run all workers concurrently
    await asyncio.gather(
        udp_receiver(shared_rssi, UDP_IP, UDP_PORT, set(anchors.keys())),
        trilateration_worker(shared_rssi, shared_raw_positions, solver),
        dbscan_worker(shared_raw_positions, shared_clean_positions, dbscan_filter),
        terminal_display_worker(shared_clean_positions),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[SERVER SHUTDOWN] Server stopped by user.")
