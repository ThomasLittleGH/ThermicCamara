import time

import numpy as np

from renderImageToWindow import render  # Import render from first file

# Properly initialize a 10x10 matrix
data = np.zeros((10, 10))

# Update entire matrix in one go (more efficient)
for y in range(10):
    for x in range(10):
        # Simulated sensor data update
        data[y, x] = np.random.uniform(20, 80)  # Replace with real sensor values

        print("Frame updated.")
        time.sleep(0.5)
        render(data)
