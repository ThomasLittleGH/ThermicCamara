import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


def generate_temperature_matrix():
    """
    Generate a random 100x100 matrix of temperature values.
    Replace this with your real data source as needed.
    """
    return np.random.uniform(20, 80, (100, 100))


# 1) Create a custom colormap: Blue -> Yellow -> Red
colors = [
    (0, 0, 1),  # Blue
    (1, 1, 0),  # Yellow
    (1, 0, 0)  # Red
]
blue_yellow_red = LinearSegmentedColormap.from_list(
    "blue_yellow_red", colors, N=256
)

# 2) Set up interactive plotting
plt.ion()
fig, ax = plt.subplots()

# Attempt full-screen
manager = plt.get_current_fig_manager()
try:
    manager.full_screen_toggle()
except AttributeError:
    pass

# Generate initial temperature data
temperature_data = generate_temperature_matrix()

# Show the data with a stable range (20°C to 80°C) so colorbar stays consistent
im = ax.imshow(
    temperature_data,
    cmap=blue_yellow_red,
    interpolation='bicubic',
    origin='lower',  # (0,0) at the bottom-left
    vmin=20,
    vmax=80
)

# Add a color bar (the side bar with temperatures)
cbar = fig.colorbar(im, ax=ax, orientation='vertical', label='Temperature (°C)')

# Remove axis labels & ticks
ax.set_xticks([])
ax.set_yticks([])

# Optional: set a title (comment out if you want no text at all)
ax.set_title('Real-Time Temperature Visualization')

# Ensure color bar and image fit nicely
plt.tight_layout()
plt.show()

# 3) Update loop
while True:
    # Generate new temperature data each second
    temperature_data = generate_temperature_matrix()

    # Update the existing image
    im.set_data(temperature_data)

    # Redraw the figure
    fig.canvas.draw_idle()

    # Pause for 1 second
    plt.pause(1)
