import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# Get screen resolution dynamically (may need adjustments based on your OS)
try:
    import screeninfo

    screen = screeninfo.get_monitors()[0]
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.width, screen.height
except:
    SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080  # Fallback default

def generate_temperature_matrix():
    """Generate a random 100x100 matrix of temperature values (Replace with actual data)."""
    return np.random.uniform(20, 80, (100, 100))  # Simulated temperature range (20°C to 80°C)

def normalize_temperature(data):
    """Normalize temperature values to range 0-255 for grayscale mapping."""
    min_temp, max_temp = data.min(), data.max()
    normalized = 255 * (1 - (data - min_temp) / (max_temp - min_temp))  # Invert: white = low temp, black = high temp
    return normalized.astype(np.uint8)


def upscale_image(image_array, width, height):
    """Upscale image using PIL's bicubic interpolation to smooth it out."""
    image = Image.fromarray(image_array)  # Convert NumPy array to PIL Image
    return image.resize((width, height), Image.BICUBIC)


# Create a Matplotlib figure for display
plt.ion()  # Enable interactive mode
fig, ax = plt.subplots()
fig.canvas.manager.set_window_title("Temperature Visualization")

while True:
    # Generate new temperature data
    temperature_data = generate_temperature_matrix()

    # Convert temperature matrix to grayscale image
    grayscale_image = normalize_temperature(temperature_data)

    # Upscale image to full screen
    upscaled_image = upscale_image(grayscale_image, SCREEN_WIDTH, SCREEN_HEIGHT)

    # Display the image using Matplotlib
    ax.clear()
    ax.imshow(upscaled_image, cmap="gray", aspect="auto")  # Show in grayscale
    ax.axis("off")  # Hide axes

    # Update the display
    plt.pause(1)  # Wait 1 second before next update

plt.ioff()  # Disable interactive mode when done
plt.show()
