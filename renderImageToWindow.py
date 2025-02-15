import matplotlib.pyplot as plt
import numpy as np

try:
    import screeninfo
    screen = screeninfo.get_monitors()[0]
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.width, screen.height
except:
    # Fallback if screeninfo is not available or fails
    SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080

def generate_temperature_matrix():
    """
    Generate a random 100x100 matrix of temperature values.
    (Replace this with your actual data source as needed.)
    """
    return np.random.uniform(20, 80, (100, 100))

def normalize_temperature(data):
    """
    Normalize temperature values to range 0-255.
    White = Hot, Black = Cold.
    """
    min_temp, max_temp = data.min(), data.max()
    normalized = 255 * ((data - min_temp) / (max_temp - min_temp))
    return normalized.astype(np.uint8)

def upscale_image(image_array, width, height):
    """
    Upscale the 100x100 image to the screen resolution using
    PIL's bicubic interpolation for smooth edges.
    """
    from PIL import Image
    image = Image.fromarray(image_array)
    return image.resize((width, height), Image.BICUBIC)


# -----------------------------------------------------------------------
#  1) Set up Matplotlib for a minimal fullscreen display
# -----------------------------------------------------------------------
plt.ion()  # Interactive mode for continuous updating
fig, ax = plt.subplots()

# Hide the toolbar (top-left of the figure)
plt.rcParams['toolbar'] = 'None'

# Attempt to make the figure fullscreen
manager = plt.get_current_fig_manager()
try:
    manager.full_screen_toggle()
except AttributeError:
    # Some backends may not have full_screen_toggle()
    # Try a generic approach:
    manager.window.state('zoomed') if hasattr(manager.window, 'state') else None

# Remove extra margins around the image
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

# Hide axes for a clean look
ax.axis("off")

# Give the window a more descriptive title (optional)
fig.canvas.manager.set_window_title("Real-Time Temperature Visualization")

# -----------------------------------------------------------------------
#  2) Main Loop: Update the visualization every second
# -----------------------------------------------------------------------
while True:
    # Generate or fetch your 100x100 temperature data
    temperature_data = generate_temperature_matrix()

    # Normalize to grayscale: White = hot, Black = cold
    grayscale_image = normalize_temperature(temperature_data)

    # Upscale the grayscale image to fit the entire screen
    upscaled_image = upscale_image(grayscale_image, SCREEN_WIDTH, SCREEN_HEIGHT)

    # Clear previous frame
    ax.clear()
    ax.axis("off")  # Keep axes hidden

    # Display the new frame
    ax.imshow(upscaled_image, cmap="gray", aspect="auto")

    # Draw and pause so the figure updates
    plt.pause(1)  # 1 second delay

plt.ioff()
plt.show()