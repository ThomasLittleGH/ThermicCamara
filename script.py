import time

import cv2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# --- User Input for Grid Size ---
width = int(input("Enter the number of pixels wide: "))
height = int(input("Enter the number of pixels tall: "))
update_delay = 0.05  # Adjust for smoother updates

# --- Webcam Setup ---
cap = cv2.VideoCapture(0)  # Adjust index if necessary
if not cap.isOpened():
    print("[ERROR] Could not access the camera.")
    exit()

# Get real webcam resolution
webcam_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
webcam_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# --- Estimated Time Calculation ---
total_updates = width * height
estimated_time = total_updates * update_delay
print(f"Estimated total rendering time: {estimated_time:.2f} seconds.")

# --- Create a Custom Colormap ---
colors = [(0, 0, 1), (1, 1, 0), (1, 0, 0)]  # Blue → Yellow → Red
blue_yellow_red = LinearSegmentedColormap.from_list("blue_yellow_red", colors, N=256)

# --- Initialize Matplotlib UI ---
plt.ion()
fig, axes = plt.subplots(1, 3, figsize=(12, 5))  # 3 Panels: Heatmap, Webcam, Data List

# Heatmap Panel
temperature_data = np.zeros((height, width))
heatmap_ax = axes[0]
heatmap_im = heatmap_ax.imshow(
    temperature_data, cmap=blue_yellow_red, interpolation='bicubic', origin='lower', vmin=20, vmax=50
)
heatmap_ax.set_title("Thermal Heatmap")
fig.colorbar(heatmap_im, ax=heatmap_ax, orientation='vertical', label='Temperature (°C)')

# Webcam Panel
webcam_ax = axes[1]
webcam_im = webcam_ax.imshow(np.zeros((webcam_height, webcam_width, 3), dtype=np.uint8))
webcam_ax.set_title("Webcam View")

# Recent Values Panel
values_ax = axes[2]
detected_values = []
values_text = values_ax.text(0.5, 0.5, "", fontsize=12, va="center", ha="center")
values_ax.set_xlim(0, 1)
values_ax.set_ylim(0, 1)
values_ax.axis("off")  # Hide axes
values_ax.set_title("Recent Values")

plt.tight_layout()
plt.show()


def update_ui():
    """ Updates all UI elements (heatmap, webcam, detected values). """
    # Update webcam frame
    ret, frame = cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert OpenCV BGR to RGB for Matplotlib
        webcam_im.set_data(frame)

    # Update heatmap
    heatmap_im.set_data(temperature_data)

    # Update recent detected values
    values_text.set_text("\n".join(map(str, detected_values[-5:])))

    # Refresh UI
    fig.canvas.draw_idle()
    plt.pause(0.01)


# --- Main Loop for Updating Pixels ---
start_time = time.time()
try:
    for y in range(height):
        for x in range(width):
            # Simulated sensor data update (replace with real sensor input)
            temperature_data[y, x] = np.random.uniform(20, 50)
            detected_values.append(np.random.randint(0, 10))  # Simulated detection

            # Update UI
            update_ui()

            # Time tracking
            elapsed_time = time.time() - start_time
            remaining_time = max(0, estimated_time - elapsed_time)
            print(f"Updated pixel ({x}, {y}) - Time remaining: {remaining_time:.2f} seconds.")

            # Check if 'Q' is pressed to quit
            if plt.waitforbuttonpress(0.01):
                print("\nQuitting rendering process...")
                break

            time.sleep(update_delay)  # Control update speed

except KeyboardInterrupt:
    print("\nProcess interrupted manually.")

# Cleanup
cap.release()
plt.ioff()
plt.show()
print("Rendering complete!")