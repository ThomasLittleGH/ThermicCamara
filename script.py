#!/usr/bin/env python3
import time
import cv2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# ==========================================================
# =============== 7-Segment Digit Parsing ==================
# ==========================================================

# Adjust threshold based on your lighting conditions.
threshold = 150

# Updated mapping table for segments (order: A, B, C, D, E, F, G)
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
    """Converts a list-of-lists of segment pixels into a number (e.g., 204 => float(204.0))."""
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
# ========= Fractional Digit Boxes & Segment Offsets ========
# ==========================================================

# Three digit boxes (normalized: left, top, right, bottom)
digit_boxes = [
    (0.17, 0.44, 0.41, 0.96),   # Digit 1
    (0.37, 0.40, 0.62, 0.93),   # Digit 2
    (0.61, 0.38, 0.82, 0.93)    # Digit 3
]

# 7 segment offsets (normalized within each digit box)
# Order: A, B, C, D, E, F, G.
segment_offsets = [
    (0.5, 0.1),   # A (top-center)
    (0.8, 0.3),   # B (upper-right)
    (0.8, 0.7),   # C (lower-right)
    (0.5, 0.9),   # D (bottom-center)
    (0.2, 0.7),   # E (lower-left)
    (0.2, 0.3),   # F (upper-left)
    (0.5, 0.5)    # G (middle-center)
]

for i, (l, t, r, b) in enumerate(digit_boxes):
    print(f"Digit {i + 1} box in fraction: left={l}, top={t}, right={r}, bottom={b}")

def extract_digit_pixels_fractional(frame_rgb: np.ndarray,
                                    digit_box: tuple[float, float, float, float],
                                    seg_offsets: list[tuple[float, float]],
                                    radius: int = 8) -> tuple[list[tuple[int, int, int]], np.ndarray]:
    """
    Given an RGB frame, a digit box in fractional coords, and segment offsets,
    compute each segment's absolute pixel coordinates. Draw a circle at each segment:
      - Green if the segment is "on" (avg intensity > threshold),
      - Red if "off."
    Returns the list of pixel values and an overlay image.
    """
    h, w = frame_rgb.shape[:2]
    left_frac, top_frac, right_frac, bottom_frac = digit_box

    box_left   = int(left_frac * w)
    box_top    = int(top_frac * h)
    box_right  = int(right_frac * w)
    box_bottom = int(bottom_frac * h)
    box_width  = box_right - box_left
    box_height = box_bottom - box_top

    # Create overlay (BGR copy) for drawing
    overlay = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    segment_pixels = []
    for (relX, relY) in seg_offsets:
        px = box_left + int(relX * box_width)
        py = box_top + int(relY * box_height)
        if 0 <= px < w and 0 <= py < h:
            pixel_rgb = frame_rgb[py, px]
            segment_pixels.append(tuple(pixel_rgb))
            avg_intensity = sum(int(c) for c in pixel_rgb) / 3.0
            # Choose color based on on/off state
            if avg_intensity > threshold:
                color = (0, 255, 0)  # green in BGR
            else:
                color = (0, 0, 255)  # red in BGR
            cv2.circle(overlay, (px, py), radius, color, -1)
        else:
            segment_pixels.append((0, 0, 0))
    return segment_pixels, overlay

def read_digits_from_frame(frame_rgb: np.ndarray,
                           digit_boxes: list[tuple[float, float, float, float]],
                           seg_offsets: list[tuple[float, float]]) -> tuple[float, np.ndarray]:
    """
    Process each digit box to extract its 7-segment pixels and recognize the digit.
    Merge the overlay images from all boxes so that all segment markers are visible.
    Build a reading string in the format "<digit1><digit2>.<digit3>".
    Returns the reading (float) and the combined overlay.
    """
    all_digit_pixels = []
    overlays = []
    for box in digit_boxes:
        seg_pixels, overlay = extract_digit_pixels_fractional(frame_rgb, box, seg_offsets)
        all_digit_pixels.append(seg_pixels)
        overlays.append(overlay)
    # Merge overlays so all markers are visible
    combined_overlay = overlays[0].copy()
    for o in overlays[1:]:
        combined_overlay = cv2.addWeighted(combined_overlay, 0.5, o, 0.5, 0)

    recognized_digits = []
    for seg_pixels in all_digit_pixels:
        d = safe_get_number([seg_pixels])
        recognized_digits.append(d)
    # Build reading string: first two digits are integer part, third is fractional.
    reading_str = f"{int(recognized_digits[0])}{int(recognized_digits[1])}.{int(recognized_digits[2])}"
    try:
        reading = float(reading_str)
    except ValueError:
        reading = 0.0
    print(f"[DEBUG] Recognized digits: {recognized_digits} -> Reading: {reading_str}")
    return reading, combined_overlay

# ==========================================================
# ======= Main Script with Heatmap & Matplotlib UI =========
# ==========================================================

def main():
    # --- User Input for Grid Size ---
    width = int(input("Enter the number of pixels wide: "))
    height = int(input("Enter the number of pixels tall: "))
    update_delay = 0.05  # Adjust for smoother updates

    # --- Webcam Setup ---
    cap = cv2.VideoCapture(0)  # Adjust index if necessary
    if not cap.isOpened():
        print("[ERROR] Could not access the camera.")
        return

    # Webcam resolution
    webcam_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    webcam_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # --- Estimated Time Calculation ---
    total_updates = width * height
    estimated_time = total_updates * update_delay
    print(f"Estimated total rendering time: {estimated_time:.2f} seconds.")

    # --- Create a Custom Colormap for the Heatmap ---
    colors = [(0, 0, 1), (1, 1, 0), (1, 0, 0)]  # Blue -> Yellow -> Red
    blue_yellow_red = LinearSegmentedColormap.from_list("blue_yellow_red", colors, N=256)

    # --- Initialize Matplotlib UI ---
    plt.ion()
    fig, axes = plt.subplots(
        2, 2, figsize=(16, 9),
        gridspec_kw={'height_ratios': [4, 1], 'width_ratios': [4, 1]}
    )

    manager = plt.get_current_fig_manager()
    try:
        manager.full_screen_toggle()
    except AttributeError:
        pass

    # --- Heatmap Panel (Larger) ---
    temperature_data = np.zeros((height, width))
    heatmap_ax = axes[0, 0]
    heatmap_im = heatmap_ax.imshow(
        temperature_data, cmap=blue_yellow_red,
        interpolation='bicubic', origin='lower', vmin=20, vmax=50
    )
    heatmap_ax.set_title("Thermal Heatmap", fontsize=14)
    fig.colorbar(heatmap_im, ax=heatmap_ax, orientation='vertical', label='Temperature (°C)')

    # --- Webcam Panel (Smaller) ---
    webcam_ax = axes[1, 0]
    webcam_im = webcam_ax.imshow(np.zeros((webcam_height, webcam_width, 3), dtype=np.uint8))
    webcam_ax.set_title("Webcam (Debug Overlay)", fontsize=12)

    # --- Recent Values Panel (Smaller) ---
    values_ax = axes[0, 1]
    detected_values = []
    values_text = values_ax.text(0.5, 0.5, "", fontsize=14, va="center", ha="center")
    values_ax.set_xlim(0, 1)
    values_ax.set_ylim(0, 1)
    values_ax.axis("off")
    values_ax.set_title("Recent Temperatures", fontsize=12)

    plt.tight_layout()
    plt.show()

    userQuit = False  # Flag for user exit

    def update_ui():
        nonlocal userQuit
        if plt.waitforbuttonpress(0.01):
            userQuit = True

        ret, frame_bgr = cap.read()
        if not ret:
            print("[WARNING] Could not read webcam frame.")
            detected_values.append(0.0)
            heatmap_im.set_data(temperature_data)
            values_text.set_text("\n".join(map(str, detected_values[-5:])))
            fig.canvas.draw_idle()
            plt.pause(0.01)
            return 0.0

        # Convert frame to RGB for processing
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        # Get reading and overlay from our three digit boxes
        reading_float, overlay_bgr = read_digits_from_frame(frame_rgb, digit_boxes, segment_offsets)
        detected_values.append(reading_float)

        # Convert overlay to RGB for Matplotlib display
        debug_rgb = cv2.cvtColor(overlay_bgr, cv2.COLOR_BGR2RGB)
        webcam_im.set_data(debug_rgb)

        heatmap_im.set_data(temperature_data)
        values_text.set_text("\n".join(f"{val:.1f}" for val in detected_values[-5:]))

        fig.canvas.draw_idle()
        plt.pause(0.01)
        return reading_float

    start_time = time.time()

    try:
        for y in range(height):
            if userQuit:
                break
            for x in range(width):
                if userQuit:
                    break
                reading_float = update_ui()
                temperature_data[y, x] = reading_float

                # Dynamically update the colormap limits.
                # We'll ignore zero values (assuming they are placeholders for unrecorded readings)
                nonzero_vals = temperature_data[temperature_data > 0]
                if nonzero_vals.size > 0:
                    current_min = np.min(nonzero_vals)
                else:
                    current_min = 20  # default minimum if no valid reading exists
                current_max = np.max(temperature_data)
                if current_max == 0:
                    current_max = 50  # default maximum if no valid reading exists
                # Prevent degenerate case:
                if current_min == current_max:
                    current_min -= 1
                    current_max += 1
                heatmap_im.set_clim(current_min, current_max)

                elapsed = time.time() - start_time
                remain = max(0, estimated_time - elapsed)
                print(f"Updated pixel ({x}, {y}) -> {reading_float:.1f} °C | Remaining: {remain:.2f}s")
                if userQuit:
                    break
                time.sleep(update_delay)
    except KeyboardInterrupt:
        print("\nProcess interrupted manually.")

    cap.release()
    plt.close('all')
    print("Rendering complete! Exiting now.")

if __name__ == "__main__":
    main()
