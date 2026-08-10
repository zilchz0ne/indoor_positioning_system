import csv
from pathlib import Path

UDP_IP = "0.0.0.0"
UDP_PORT = 4210
WS_PORT = 8765
PLATFORM_FT = 4.0


def load_anchors(file_path: str = "anchor_config.csv") -> dict[str, dict]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Anchor configuration file '{file_path}' not found.")

    anchors = {}
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mac = row["mac"].strip().lower()
            anchors[mac] = {
                "name": row["name"].strip(),
                "x": float(row["x"]),
                "y": float(row["y"]),
                "tx": float(row["tx"]),
                "n": float(row["n"]),
            }
    return anchors
