import socket
import json
import matplotlib.pyplot as plt

# ---------------- UDP ----------------
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", 4210))

# ---------------- PLOT ----------------
plt.ion()
fig, ax = plt.subplots()

# anchor positions (must match ESP)
Ax, Ay = -0.5, 0
Bx, By = 0.0, 1.0
Cx, Cy = 0.5, 0

while True:
    data, _ = sock.recvfrom(1024)

    try:
        msg = data.decode().strip()
        if not (msg.startswith("{") and msg.endswith("}")):
            continue

        obj = json.loads(msg)

        # candidate points
        p1 = obj["points"][0]
        p2 = obj["points"][1]

        # methods
        final = obj["final"]
        tri = obj["tri"]

        x1, y1 = p1["x"], p1["y"]
        x2, y2 = p2["x"], p2["y"]

        fx, fy = final["x"], final["y"]
        tx, ty = tri["x"], tri["y"]

        # clear
        ax.clear()

        # ---- anchors ----
        ax.scatter([Ax, Bx, Cx], [Ay, By, Cy])
        ax.text(Ax, Ay, "A")
        ax.text(Bx, By, "B")
        ax.text(Cx, Cy, "C")

        # ---- candidate points (very faint) ----
        ax.scatter(x1, y1, alpha=0.2)
        ax.scatter(x2, y2, alpha=0.2)

        # ---- your method (final) ----
        ax.scatter(fx, fy, s=100)
        ax.text(fx, fy, "Final")

        # ---- trilateration ----
        ax.scatter(tx, ty, marker='x', s=100)
        ax.text(tx, ty, "Tri")

        # ---- styling ----
        ax.set_xlim(-3, 3)
        ax.set_ylim(-3, 3)
        ax.set_aspect('equal')
        ax.set_title("Indoor Positioning: Final vs Trilateration")

        plt.pause(0.01)

    except:
        pass
