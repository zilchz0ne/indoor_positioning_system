"""
display.py
----------
Lightweight console output worker that reads clean, DBSCAN-filtered 
positions from Conveyor Belt 3 and prints them directly to stdout.
"""

import asyncio
from typing import Dict, Any, Optional


async def terminal_display_worker(shared_clean_positions: Dict[str, Optional[Dict[str, Any]]]):
    """Periodically prints the latest filtered target position to the terminal."""
    print("\n[DISPLAY] Target Tracking Active (Press Ctrl+C to stop)...\n")
    
    while True:
        pos = shared_clean_positions.get("T1")
        if pos:
            status_tag = "FILTERED" if pos.get("is_filtered") else "RAW_MEAN"
            print(f"[POS UPDATE] Target: {pos['target_id']} | X: {pos['x']:.2f} ft | Y: {pos['y']:.2f} ft | Status: [{status_tag}]")
        else:
            print("[POS UPDATE] Searching for target... (Waiting for active signals)")

        # Update console display every 200 ms (5 Hz)
        await asyncio.sleep(0.2)
