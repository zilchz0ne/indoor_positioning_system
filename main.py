import socket
import json
import matplotlib.pyplot as plt

# ---------------- UDP ----------------
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", 4210))

# ---------------- PLOT ----------------
plt.ion()
fig, ax = plt.subplots()

while True:
    data, _ = sock.recvfrom(1024)

    try:
        msg = data.decode().strip()
        if not (msg.startswith("{") and msg.endswith("}")):
            continue

        obj = json.loads(msg)

        p1 = obj["points"][0]
        p2 = obj["points"][1]

        x1, y1 = p1["x"], p1["y"]
        x2, y2 = p2["x"], p2["y"]

        # clear and redraw
        ax.clear()

        # anchors (fixed)
        ax.scatter([-0.5, 0.5], [0, 0])  # A and C
        ax.text(-0.5, 0, "A")
        ax.text(0.5, 0, "C")

        # candidate points
        ax.scatter(x1, y1)
        ax.scatter(x2, y2)

        # styling
        ax.set_xlim(-3, 3)
        ax.set_ylim(-3, 3)
        ax.set_aspect('equal')
        ax.set_title("Indoor Positioning (2-anchor)")

        plt.pause(0.01)

    except:
        pass
