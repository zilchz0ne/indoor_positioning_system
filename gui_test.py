import matplotlib
matplotlib.use('TkAgg') # Forces the Tkinter GUI engine
import matplotlib.pyplot as plt

print("Initializing basic plot test...")
fig, ax = plt.subplots(figsize=(6, 6))

# Draw some test static anchors
ax.scatter([-0.5, 0.0, 0.5], [0.0, 1.0, 0.0], color='red', s=100)
ax.text(-0.5, 0.0, " A")
ax.text(0.0, 1.0, " B")
ax.text(0.5, 0.0, " C")

ax.set_xlim(-3, 3)
ax.set_ylim(-3, 3)
ax.set_title("If you see this, your Linux GUI is 100% Working!")
ax.grid(True)

print("Showing window... (Close the window to exit)")
plt.show() # This blocks and keeps the window open until you click close
