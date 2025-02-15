import time

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# --- User Input for Grid Size ---
width = int(input("Enter the number of pixels wide: "))
height = int(input("Enter the number of pixels tall: "))
update_delay = 0.51  # Time delay per pixel update (adjust as needed)

# --- Estimated Time Calculation ---
total_updates = width * height
estimated_time = total_updates * update_delay
print(f"Estimated total rendering time: {estimated_time:.2f} seconds.")

# --- Create a Custom Colormap ---
colors = [
    (0, 0, 1),  # Blue
    (1, 1, 0),  # Yellow
    (1, 0, 0)  # Red
]
blue_yellow_red = LinearSegmentedColormap.from_list("blue_yellow_red", colors, N=256)

# --- Set Up Interactive Plotting ---
plt.ion()
fig, ax = plt.subplots()

# Attempt full-screen mode
manager = plt.get_current_fig_manager()
try:
    manager.full_screen_toggle()
except AttributeError:
    pass

# Initialize a blank matrix based on user input
temperature_data = np.zeros((height, width))

im = ax.imshow(
    temperature_data,
    cmap=blue_yellow_red,
    interpolation='bicubic',
    origin='lower',
    vmin=20,
    vmax=50
)

# Add a color bar
cbar = fig.colorbar(im, ax=ax, orientation='vertical', label='Temperature (°C)')

# Ensure layout fits
plt.tight_layout()
plt.show()


def render(temperature_data, remaining_time):
    """Update the image with new temperature data and update the title."""
    im.set_data(temperature_data)
    ax.set_title(f"Time Remaining: {remaining_time:.2f}s | Press 'Q' to Quit", fontsize=12)
    fig.canvas.draw_idle()
    plt.pause(0.01)  # Allows real-time updates


# --- Main Loop for Updating Pixels ---
start_time = time.time()
try:
    for y in range(height):
        for x in range(width):
            # Simulated sensor data update (replace with real sensor input)
            temperature_data[y, x] = np.random.uniform(20, 50)

            # Time tracking
            elapsed_time = time.time() - start_time
            remaining_time = max(0, estimated_time - elapsed_time)

            # Render updated frame
            render(temperature_data, remaining_time)

            # Print update status
            print(f"Updated pixel ({x}, {y}) - Time remaining: {remaining_time:.2f} seconds.")

            # Check if 'Q' is pressed using Matplotlib's key press detection
            if plt.waitforbuttonpress(0.01):  # Checks for any keypress
                print("\nQuitting rendering process...")
                break

            # Delay for real-time effect
            time.sleep(update_delay)

except KeyboardInterrupt:
    print("\nProcess interrupted manually.")
    exit(0)

print("Rendering complete!")
