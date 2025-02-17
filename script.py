#!/usr/bin/env python3
import threading
import time
from io import BytesIO

import cv2
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, Response, render_template_string
from matplotlib.colors import LinearSegmentedColormap

matplotlib.use('Agg')

# ==========================================================
# Global Configuration and Variables
# ==========================================================
GRID_WIDTH = 10  # Number of horizontal grid cells
GRID_HEIGHT = 10  # Number of vertical grid cells
update_delay = 0.05  # Delay between cell updates during heatmap generation

# Global arrays to hold the temperature readings and webcam frame
temperature_data = np.zeros((GRID_HEIGHT, GRID_WIDTH))
latest_reading = 0.0
latest_frame = None  # Latest webcam frame (BGR format)

# Flag to control heatmap generation (one scan at a time)
heatmap_running = False

# ==========================================================
# 7-Segment Digit Parsing Functions
# ==========================================================
threshold = 150  # Adjust based on your lighting conditions

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
    bool_list = []
    for pixel in pixel_list:
        avg_intensity = sum(int(c) for c in pixel) / 3.0
        bool_list.append(avg_intensity > threshold)
    return bool_list

def ReturnSingleNumber(bool_list: list[bool]) -> int:
    pattern = tuple(bool_list)
    return values.get(pattern, -1)

def GetNumber(numbers: list[list[tuple[int, int, int]]]) -> float:
    digits = []
    for pixel_list in numbers:
        bool_list = GetBoolValues(pixel_list)
        digit = ReturnSingleNumber(bool_list)
        if digit == -1:
            raise ValueError("Digit pattern not found!")
        digits.append(str(digit))
    return float("".join(digits))

def safe_get_number(numbers: list[list[tuple[int, int, int]]]) -> float:
    try:
        return GetNumber(numbers)
    except ValueError:
        return 0.0

# ==========================================================
# Fractional Digit Boxes & Segment Offsets
# ==========================================================
digit_boxes = [
    (0.17, 0.44, 0.41, 0.96),  # Digit 1
    (0.37, 0.40, 0.62, 0.93),  # Digit 2
    (0.61, 0.38, 0.82, 0.93)  # Digit 3
]

segment_offsets = [
    (0.5, 0.1),  # A (top-center)
    (0.8, 0.3),  # B (upper-right)
    (0.8, 0.7),  # C (lower-right)
    (0.5, 0.9),  # D (bottom-center)
    (0.2, 0.7),  # E (lower-left)
    (0.2, 0.3),  # F (upper-left)
    (0.5, 0.5)  # G (middle-center)
]


def extract_digit_pixels_fractional(frame_rgb: np.ndarray,
                                    digit_box: tuple[float, float, float, float],
                                    seg_offsets: list[tuple[float, float]],
                                    radius: int = 8) -> tuple[list[tuple[int, int, int]], np.ndarray]:
    h, w = frame_rgb.shape[:2]
    left_frac, top_frac, right_frac, bottom_frac = digit_box
    box_left = int(left_frac * w)
    box_top = int(top_frac * h)
    box_right = int(right_frac * w)
    box_bottom = int(bottom_frac * h)
    box_width = box_right - box_left
    box_height = box_bottom - box_top

    overlay = frame_rgb.copy()  # Dummy overlay (unused in web version)
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
# Flask Web Server and Background Threads
# ==========================================================
app = Flask(__name__)

# Create a custom colormap (Blue -> Yellow -> Red)
colors = [(0, 0, 1), (1, 1, 0), (1, 0, 0)]
blue_yellow_red = LinearSegmentedColormap.from_list("blue_yellow_red", colors, N=256)


@app.route('/')
def index():
    # Place heatmap and webcam feed side by side.
    html = '''
    <html>
      <head>
        <title>Thermal Heatmap & Webcam Feed</title>
      </head>
      <body>
        <h1>Thermal Heatmap & Webcam Feed</h1>
        <table>
          <tr>
            <td>
              <h2>Thermal Heatmap</h2>
              <img src="/heatmap.png" alt="Heatmap"/>
              <br/>
              <button onclick="startScan()">Start Scan</button>
              <span id="scanStatus"></span>
            </td>
            <td>
              <h2>Webcam Feed</h2>
              <img src="/video_feed" alt="Webcam Feed" style="max-width:640px;"/>
            </td>
          </tr>
        </table>
        <p>Latest reading: {{latest}}</p>
        <p>
          <a href="/servo/left">Move Servo Left</a> |
          <a href="/servo/right">Move Servo Right</a> |
          <a href="/servo/stop">Stop Servo</a>
        </p>
        <script>
          function startScan() {
            document.getElementById("scanStatus").innerHTML = "Scan started...";
            fetch('/heatmap/start')
              .then(response => response.text())
              .then(data => {
                document.getElementById("scanStatus").innerHTML = data;
              })
              .catch(error => {
                document.getElementById("scanStatus").innerHTML = "Error starting scan";
              });
          }
        </script>
      </body>
    </html>
    '''
    return render_template_string(html, latest=latest_reading)


@app.route('/heatmap.png')
def heatmap_png():
    # Generate a heatmap image from the current temperature_data array.
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


@app.route('/video_feed')
def video_feed():
    return Response(gen_video_feed(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/servo/left')
def servo_left():
    move_servo_left()
    return "Servo moved left (dummy)."


@app.route('/servo/right')
def servo_right():
    move_servo_right()
    return "Servo moved right (dummy)."


@app.route('/servo/stop')
def servo_stop():
    stop_servo()
    return "Servo stopped (dummy)."


@app.route('/heatmap/start')
def heatmap_start():
    global heatmap_running
    if not heatmap_running:
        threading.Thread(target=generate_heatmap, daemon=True).start()
        return "Scan started."
    else:
        return "Scan already running."


def gen_video_feed():
    """Generator that yields the latest webcam frame as a JPEG image."""
    global latest_frame
    while True:
        if latest_frame is None:
            time.sleep(0.1)
            continue
        ret, jpeg = cv2.imencode('.jpg', latest_frame)
        if not ret:
            continue
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.05)


def camera_loop():
    """Continuously capture frames from the camera for the webcam feed."""
    global latest_frame
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not access the camera.")
        return
    try:
        while True:
            ret, frame_bgr = cap.read()
            if not ret:
                continue
            latest_frame = frame_bgr.copy()
            time.sleep(0.05)
    except Exception as e:
        print("Camera loop exception:", e)
    finally:
        cap.release()


def generate_heatmap():
    """
    Generate one heatmap update over the grid in snake pattern.
    Updates temperature_data cell by cell. This function stops when complete.
    """
    global heatmap_running, temperature_data, latest_reading
    heatmap_running = True
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not access the camera for heatmap generation.")
        heatmap_running = False
        return
    try:
        for y in range(GRID_HEIGHT):
            if not heatmap_running:
                break
            x_range = range(GRID_WIDTH) if y % 2 == 0 else range(GRID_WIDTH - 1, -1, -1)
            for x in x_range:
                if not heatmap_running:
                    break
                ret, frame_bgr = cap.read()
                if not ret:
                    continue
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                reading = read_digits_from_frame(frame_rgb, digit_boxes, segment_offsets)
                temperature_data[y, x] = reading
                latest_reading = reading
                time.sleep(update_delay)
    except Exception as e:
        print("Heatmap generation exception:", e)
    finally:
        cap.release()
        heatmap_running = False
    print("Scan complete.")


if __name__ == '__main__':
    # Start the continuous camera loop for the webcam feed.
    threading.Thread(target=camera_loop, daemon=True).start()
    # Run the Flask app on all interfaces (useful for a Pi accessed via SSH)
    app.run(host='0.0.0.0', port=5000)
