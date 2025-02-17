#!/usr/bin/env python3
import time
import cv2
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from flask import Flask, Response, render_template_string
import threading
from io import BytesIO
import matplotlib.pyplot as plt

# ==========================================================
# Global Configuration and Variables
# ==========================================================
GRID_WIDTH = 10     # Set the number of horizontal pixels
GRID_HEIGHT = 10    # Set the number of vertical pixels
update_delay = 0.05  # Delay between updates

# Global arrays to hold the temperature readings
temperature_data = np.zeros((GRID_HEIGHT, GRID_WIDTH))
latest_reading = 0.0

# ==========================================================
# 7-Segment Digit Parsing Functions
# ==========================================================
# Adjust threshold based on your lighting conditions.
threshold = 150

# Mapping table for segments (order: A, B, C, D, E, F, G)
values = {
    (True, True, True, True, True, True, False): 0,
    (False, True, True, False, False, False, False): 1,
    (True, True, False, True, True, False, True): 2,
    (True, True, True, True, False, False, True): 3,
    (False, True, True, False, False, True, True): 4,
    (True, False, True, True, False, True, True): 5,
    (True, False, True, True, True, True, True): 6,
    (True, True, True, False, False, False, False): 7,
    (True, True, True, True, True, True, True): 8,
    (True, True, True, True, False, True, True): 9
}

def GetBoolValues(pixel_list: list[tuple[int, int, int]]) -> list[bool]:
    """Convert each (R,G,B) pixel to True if its average exceeds threshold."""
    bool_list = []
    for pixel in pixel_list:
        avg_intensity = sum(int(c) for c in pixel) / 3.0
        val = avg_intensity > threshold
        print(f"[DEBUG] Pixel {pixel} -> avg={avg_intensity:.1f}, threshold={threshold} => {val}")
        bool_list.append(val)
    return bool_list

def ReturnSingleNumber(bool_list: list[bool]) -> int:
    """Convert a 7-element boolean list into a digit using the lookup table."""
    pattern = tuple(bool_list)
    digit = values.get(pattern, -1)
    print(f"[DEBUG] 7-seg pattern {pattern} => recognized digit: {digit}")
    return digit

def GetNumber(numbers: list[list[tuple[int, int, int]]]) -> float:
    """Converts a list-of-lists of segment pixels into a number (e.g., 204 -> float(204.0))."""
    digits = []
    for pixel_list in numbers:
        bool_list = GetBoolValues(pixel_list)
        digit = ReturnSingleNumber(bool_list)
        if digit == -1:
            raise ValueError("Digit pattern not found!")
        digits.append(str(digit))
    return float("".join(digits))

def safe_get_number(numbers: list[list[tuple[int, int, int]]]) -> float:
    """Same as GetNumber, but returns 0.0 if any digit is unrecognized."""
    try:
        return GetNumber(numbers)
    except ValueError:
        return 0.0

# ==========================================================
# Fractional Digit Boxes & Segment Offsets
# ==========================================================
# Three digit boxes (normalized coordinates: left, top, right, bottom)
digit_boxes = [
    (0.17, 0.44, 0.41, 0.96),   # Digit 1
    (0.37, 0.40, 0.62, 0.93),   # Digit 2
    (0.61, 0.38, 0.82, 0.93)    # Digit 3
]

# 7-segment offsets (normalized within each digit box; order: A, B, C, D, E, F, G)
segment_offsets = [
    (0.5, 0.1),   # A (top-center)
    (0.8, 0.3),   # B (upper-right)
    (0.8, 0.7),   # C (lower-right)
    (0.5, 0.9),   # D (bottom-center)
    (0.2, 0.7),   # E (lower-left)
    (0.2, 0.3),   # F (upper-left)
    (0.5, 0.5)    # G (middle-center)
]

def extract_digit_pixels_fractional(frame_rgb: np.ndarray,
                                    digit_box: tuple[float, float, float, float],
                                    seg_offsets: list[tuple[float, float]],
                                    radius: int = 8) -> tuple[list[tuple[int, int, int]], np.ndarray]:
    """
    Given an RGB frame, a digit box (in fractional coordinates), and segment offsets,
    compute each segment's absolute pixel coordinates.
    Returns the list of pixel values and an overlay image (here unused in the web version).
    """
    h, w = frame_rgb.shape[:2]
    left_frac, top_frac, right_frac, bottom_frac = digit_box
    box_left   = int(left_frac * w)
    box_top    = int(top_frac * h)
    box_right  = int(right_frac * w)
    box_bottom = int(bottom_frac * h)
    box_width  = box_right - box_left
    box_height = box_bottom - box_top

    # Create a dummy overlay (unused here)
    overlay = frame_rgb.copy()
    segment_pixels = []
    for (relX, relY) in seg_offsets:
        px = box_left + int(relX * box_width)
        py = box_top + int(relY * box_height)
        if 0 <= px < w and 0 <= py < h:
            pixel_rgb = frame_rgb[py, px]
            segment_pixels.append(tuple(pixel_rgb))
        else:
            segment_pixels.append((0, 0, 0))
    return segment_pixels, overlay

def read_digits_from_frame(frame_rgb: np.ndarray,
                           digit_boxes: list[tuple[float, float, float, float]],
                           seg_offsets: list[tuple[float, float]]) -> float:
    """
    Process each digit box to extract its 7-segment pixels and recognize the digit.
    Builds a reading string in the format "<digit1><digit2>.<digit3>".
    Returns the recognized reading as a float.
    """
    all_digit_pixels = []
    for box in digit_boxes:
        seg_pixels, _ = extract_digit_pixels_fractional(frame_rgb, box, seg_offsets)
        all_digit_pixels.append(seg_pixels)
    recognized_digits = []
    for seg_pixels in all_digit_pixels:
        d = safe_get_number([seg_pixels])
        recognized_digits.append(d)
    reading_str = f"{int(recognized_digits[0])}{int(recognized_digits[1])}.{int(recognized_digits[2])}"
    try:
        reading = float(reading_str)
    except ValueError:
        reading = 0.0
    print(f"[DEBUG] Recognized digits: {recognized_digits} -> Reading: {reading_str}")
    return reading

# ==========================================================
# Dummy Servo Functions
# ==========================================================
def move_servo_left():
    print("Dummy: Moving servo left")

def move_servo_right():
    print("Dummy: Moving servo right")

def stop_servo():
    print("Dummy: Stopping servo")

# ==========================================================
# Flask Web Server and Background Camera Loop
# ==========================================================
app = Flask(__name__)

# Create a custom colormap (Blue -> Yellow -> Red)
colors = [(0, 0, 1), (1, 1, 0), (1, 0, 0)]
blue_yellow_red = LinearSegmentedColormap.from_list("blue_yellow_red", colors, N=256)

@app.route('/')
def index():
    # Simple HTML page that auto-refreshes every 5 seconds
    html = '''
    <html>
      <head>
        <title>Thermal Heatmap</title>
        <meta http-equiv="refresh" content="5">
      </head>
      <body>
        <h1>Thermal Heatmap</h1>
        <img src="/heatmap.png" alt="Heatmap"/><br>
        <p>Latest reading: {{latest}}</p>
        <p>
          <a href="/servo/left">Move Servo Left</a> |
          <a href="/servo/right">Move Servo Right</a> |
          <a href="/servo/stop">Stop Servo</a>
        </p>
      </body>
    </html>
    '''
    return render_template_string(html, latest=latest_reading)

@app.route('/heatmap.png')
def heatmap_png():
    # Generate a heatmap image from the current temperature_data array
    fig, ax = plt.subplots()
    nonzero_vals = temperature_data[temperature_data > 0]
    current_min = np.min(nonzero_vals) if nonzero_vals.size > 0 else 20
    current_max = np.max(temperature_data) if np.max(temperature_data) > 0 else 50
    if current_min == current_max:
        current_min -= 1
        current_max += 1
    im = ax.imshow(temperature_data, cmap=blue_yellow_red,
                   interpolation='bicubic', origin='lower',
                   vmin=current_min, vmax=current_max)
    ax.set_title("Thermal Heatmap")
    plt.colorbar(im, ax=ax)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return Response(buf.getvalue(), mimetype='image/png')

@app.route('/servo/left')
def servo_left():
    move_servo_left()
    return "Servo moved left (dummy). <a href='/'>Back</a>"

@app.route('/servo/right')
def servo_right():
    move_servo_right()
    return "Servo moved right (dummy). <a href='/'>Back</a>"

@app.route('/servo/stop')
def servo_stop():
    stop_servo()
    return "Servo stopped (dummy). <a href='/'>Back</a>"

def camera_loop():
    """Continuously capture frames from the camera and update the heatmap."""
    global latest_reading, temperature_data
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not access the camera.")
        return
    try:
        while True:
            for y in range(GRID_HEIGHT):
                # Use snake pattern: left-to-right for even rows, right-to-left for odd rows
                x_range = range(GRID_WIDTH) if y % 2 == 0 else range(GRID_WIDTH - 1, -1, -1)
                for x in x_range:
                    ret, frame_bgr = cap.read()
                    if not ret:
                        continue
                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    reading = read_digits_from_frame(frame_rgb, digit_boxes, segment_offsets)
                    temperature_data[y, x] = reading
                    latest_reading = reading
                    time.sleep(update_delay)
    except Exception as e:
        print("Camera loop exception:", e)
    finally:
        cap.release()

if __name__ == '__main__':
    # Start the camera loop in a background thread
    cam_thread = threading.Thread(target=camera_loop, daemon=True)
    cam_thread.start()
    # Run the Flask app on all interfaces (useful for a Pi accessed via SSH)
    app.run(host='0.0.0.0', port=5000)
