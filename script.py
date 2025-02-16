import time

import cv2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# ==========================================================
# =============== 7-Segment Digit Parsing ==================
# ==========================================================

threshold = 150  # Average pixel intensity above this is considered "white" (True)

# Map of 7-segment boolean patterns to digits 0-9
values = {
    (True, True, True, False, True, True, True): 0,
    (False, False, True, False, False, True, False): 1,
    (True, False, True, True, True, False, True): 2,
    (True, False, True, True, False, True, True): 3,
    (False, True, True, True, False, True, False): 4,
    (True, True, False, True, False, True, True): 5,
    (True, True, False, True, True, True, True): 6,
    (True, False, True, False, False, True, False): 7,
    (True, True, True, True, True, True, True): 8,
    (True, True, True, True, False, True, False): 9
}


def GetBoolValues(pixel_list: list[tuple[int, int, int]]) -> list[bool]:
    """
    Converts each (R,G,B) pixel into True/False based on threshold.
    """
    bool_list = []
    for pixel in pixel_list:
        avg_intensity = sum(pixel) / 3.0
        bool_list.append(avg_intensity > threshold)
    return bool_list


def ReturnSingleNumber(bool_list: list[bool]) -> int:
    """
    Takes a 7-element bool list and returns a digit (0-9).
    Returns -1 if the pattern is not in 'values'.
    """
    return values.get(tuple(bool_list), -1)


def GetNumber(numbers: list[list[tuple[int, int, int]]]) -> float:
    """
    Converts multiple 7-segment pixel-lists into a float.
    E.g., three digits => '204' => float(204.0).
    """
    digits = []
    for pixel_list in numbers:
        bool_list = GetBoolValues(pixel_list)
        digit = ReturnSingleNumber(bool_list)
        if digit == -1:
            raise ValueError("Digit pattern not found!")
        digits.append(str(digit))
    return float("".join(digits))


def safe_get_number(numbers: list[list[tuple[int, int, int]]]) -> float:
    """
    Same as GetNumber, but returns 0.0 if a digit is unrecognized.
    """
    try:
        return GetNumber(numbers)
    except ValueError:
        return 0.0


# ==========================================================
# ========= Fractional Digit Boxes & Segment Offsets ======
# ==========================================================

"""
We define 3 digit "boxes" in fractional coordinates:
(left, top, right, bottom) for each digit.
Example: digit1_box = (0.05, 0.2, 0.15, 0.5)

Inside each digit box, we define 7 "segment offsets" in [0..1, 0..1].
We assume a 7-segment shape, so we place them roughly:
   A = top-center, B = top-right, C = bottom-right,
   D = bottom-center, E = bottom-left, F = top-left, G = middle-center
Adjust these to match your real 7-segment positions.
"""

# 3 bounding boxes for 3 digits, near top-right
digit_boxes = [
    (0.25, 0.10, 0.43, 0.75),  # Digit 1
    (0.43, 0.10, 0.63, 0.75),  # Digit 2
    (0.63, 0.10, 0.83, 0.75)  # Digit 3
]

# 7 segments (fractional offsets). Tweak as needed!
segment_offsets = [
    (0.5, 0.1),  # A (top-center)
    (0.8, 0.3),  # B (upper-right)
    (0.8, 0.7),  # C (lower-right)
    (0.5, 0.9),  # D (bottom-center)
    (0.2, 0.7),  # E (lower-left)
    (0.2, 0.3),  # F (upper-left)
    (0.5, 0.5)  # G (middle-center)
]

for i, (l, t, r, b) in enumerate(digit_boxes):
    print(f"Digit {i + 1} box in fraction: left={l}, top={t}, right={r}, bottom={b}")


def extract_digit_pixels_fractional(
        frame_rgb: np.ndarray,
        digit_box: tuple[float, float, float, float],
        seg_offsets: list[tuple[float, float]],
        color_bgr: tuple[int, int, int] = (255, 0, 0),
        radius: int = 8
) -> list[tuple[int, int, int]]:
    """
    Given a frame (RGB), a digit box in fractional coords (left, top, right, bottom),
    and a list of 7 segment offsets (fractional),
    we compute each segment's absolute pixel in the frame,
    draw a debug circle in 'color_bgr',
    and return the list of (R,G,B) values for those 7 segments.
    """
    h, w = frame_rgb.shape[:2]
    left_frac, top_frac, right_frac, bottom_frac = digit_box

    # Convert bounding box fractions to absolute pixel coords
    box_left = int(left_frac * w)
    box_top = int(top_frac * h)
    box_right = int(right_frac * w)
    box_bottom = int(bottom_frac * h)

    box_width = box_right - box_left
    box_height = box_bottom - box_top

    # We'll draw on a BGR copy for debug
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

    segment_pixels = []
    for (relX, relY) in seg_offsets:
        px = box_left + int(relX * box_width)
        py = box_top + int(relY * box_height)

        # If (px, py) is in range, read the pixel from frame_rgb
        if 0 <= px < w and 0 <= py < h:
            pixel_rgb = frame_rgb[py, px]  # (R,G,B)
            segment_pixels.append(tuple(pixel_rgb))
            cv2.circle(frame_bgr, (px, py), radius, color_bgr, -1)
        else:
            # Out of range => black or skip
            segment_pixels.append((0, 0, 0))

    return segment_pixels, frame_bgr


def read_thermometer(frame_rgb: np.ndarray) -> float:
    """
    Reads 3 digits from the thermometer using fractional bounding boxes.
    Returns a float like "20.4" or "204" if decimal logic is not used.
    """

    # For debug, we'll keep merging the BGR overlays from each digit
    merged_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

    # We parse 3 digits, storing each in a list-of-lists for 7 segments
    all_digit_pixels = []
    digit_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # BGR for each digit

    for i, digit_box in enumerate(digit_boxes):
        seg_pixels, digit_bgr = extract_digit_pixels_fractional(
            frame_rgb, digit_box, segment_offsets,
            color_bgr=digit_colors[i % len(digit_colors)],
            radius=8
        )
        all_digit_pixels.append(seg_pixels)

        # Merge the drawn circles onto merged_bgr
        merged_bgr = cv2.addWeighted(merged_bgr, 0.7, digit_bgr, 0.3, 0)

    # Convert each digit’s 7 pixels into a single number
    # (If you want multiple digits => [digit1, digit2, digit3], then parse them together)
    val1 = safe_get_number([all_digit_pixels[0]])  # float
    val2 = safe_get_number([all_digit_pixels[1]])
    val3 = safe_get_number([all_digit_pixels[2]])

    # Build a reading, e.g. "val1val2.val3" => "201.5" or whatever
    reading_str = f"{int(val1)}{int(val2)}.{int(val3)}"
    try:
        reading_float = float(reading_str)
    except ValueError:
        reading_float = 0.0

    return reading_float, merged_bgr


# ==========================================================
# ======= Now The Main Script with Heatmap & Matplotlib ====
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

    # --- Create a Custom Colormap ---
    colors = [(0, 0, 1), (1, 1, 0), (1, 0, 0)]  # Blue → Yellow → Red
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
    values_ax.set_title("Temperaturas recientes", fontsize=12)

    plt.tight_layout()
    plt.show()

    userQuit = False  # Flag to track if the user pressed a key to quit

    def update_ui():
        nonlocal userQuit

        # Check if user pressed any key in the figure
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

        # Convert to RGB for fractional bounding logic
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # Attempt reading thermometer
        reading_float, overlay_bgr = read_thermometer(frame_rgb)
        detected_values.append(reading_float)

        # Show debug overlay in Matplotlib (convert overlay_bgr->RGB)
        debug_rgb = cv2.cvtColor(overlay_bgr, cv2.COLOR_BGR2RGB)
        webcam_im.set_data(debug_rgb)

        # Update heatmap & recent values
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

                # 1) New reading
                reading_float = update_ui()

                # 2) Store in heatmap
                temperature_data[y, x] = reading_float

                # 3) Print status
                elapsed = time.time() - start_time
                remain = max(0, estimated_time - elapsed)
                print(f"Updated pixel ({x}, {y}) -> {reading_float:.1f} °C | Remaining: {remain:.2f}s")

                # 4) If user pressed a key
                if userQuit:
                    break

                time.sleep(update_delay)

    except KeyboardInterrupt:
        print("\nProcess interrupted manually.")

    # Cleanup
    cap.release()
    plt.close('all')
    print("Rendering complete! Exiting now.")


if __name__ == "__main__":
    main()
