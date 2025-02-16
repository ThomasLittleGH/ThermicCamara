#!/usr/bin/env python3
import cv2
import numpy as np

# -----------------------------
# 7-Segment Parsing Parameters
# -----------------------------
threshold = 150  # Adjust based on your lighting

# Mapping from 7-seg pattern (A,B,C,D,E,F,G) to digit
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

def GetBoolValues(pixel_list):
    """
    Given a list of (R, G, B) pixel values, return a list of booleans.
    A segment is "on" if its average intensity exceeds the threshold.
    """
    bool_list = []
    for pixel in pixel_list:
        avg_intensity = sum(int(c) for c in pixel) / 3.0
        val = avg_intensity > threshold
        print(f"[DEBUG] Pixel {pixel} -> avg={avg_intensity:.1f}, threshold={threshold} => {val}")
        bool_list.append(val)
    return bool_list

def ReturnSingleNumber(bool_list):
    """
    Convert the 7-element boolean list into a digit using our lookup table.
    """
    pattern = tuple(bool_list)
    digit = values.get(pattern, -1)
    print(f"[DEBUG] 7-seg pattern {pattern} => recognized digit: {digit}")
    return digit

def safe_get_number(numbers):
    """
    Given a list-of-lists (each inner list representing one digit’s segments),
    convert each into a recognized digit and then concatenate them.
    """
    try:
        digits = []
        for pixel_list in numbers:
            bool_list = GetBoolValues(pixel_list)
            d = ReturnSingleNumber(bool_list)
            if d == -1:
                raise ValueError("Unrecognized digit pattern")
            digits.append(str(d))
        return float("".join(digits))
    except ValueError:
        return 0.0

# -----------------------------
# Digit Box & Segment Offsets
# -----------------------------
# Three digit boxes in normalized coordinates (left, top, right, bottom)
digit_boxes = [
    (0.16, 0.44, 0.40, 0.96),   # Digit 1
    (0.36, 0.40, 0.61, 0.93),   # Digit 2
    (0.6,   0.38, 0.81, 0.93)    # Digit 3
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

def extract_digit_pixels_fractional(frame_rgb, digit_box, seg_offsets, radius=8):
    """
    Given an RGB frame, a digit box (fractional coords), and segment offsets,
    compute the absolute pixel positions for each segment.
    Draw a circle at each position:
      - Green if the segment's average intensity > threshold,
      - Red otherwise.
    Returns the list of (R, G, B) pixel values and an overlay image.
    """
    h, w = frame_rgb.shape[:2]
    left_frac, top_frac, right_frac, bottom_frac = digit_box

    box_left   = int(left_frac * w)
    box_top    = int(top_frac * h)
    box_right  = int(right_frac * w)
    box_bottom = int(bottom_frac * h)
    box_width  = box_right - box_left
    box_height = box_bottom - box_top

    overlay = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    segment_pixels = []
    for (relX, relY) in seg_offsets:
        px = box_left + int(relX * box_width)
        py = box_top + int(relY * box_height)
        if 0 <= px < w and 0 <= py < h:
            pixel_rgb = frame_rgb[py, px]
            segment_pixels.append(tuple(pixel_rgb))
            avg_intensity = sum(int(c) for c in pixel_rgb) / 3.0
            # Green if on, Red if off.
            if avg_intensity > threshold:
                color = (0, 255, 0)  # green in BGR
            else:
                color = (0, 0, 255)  # red in BGR
            cv2.circle(overlay, (px, py), radius, color, -1)
        else:
            segment_pixels.append((0, 0, 0))
    return segment_pixels, overlay

def read_digits_from_frame(frame_rgb, digit_boxes, seg_offsets):
    """
    For each digit box, extract the 7-segment pixels and recognize the digit.
    Also, merge the overlay images from all digit boxes so that points for all
    digits are visible.
    Then, build a reading string in the format "<digit1><digit2>.<digit3>".
    Returns the reading (as float) and the combined overlay.
    """
    all_digit_pixels = []
    overlays = []
    for box in digit_boxes:
        seg_pixels, overlay = extract_digit_pixels_fractional(frame_rgb, box, seg_offsets)
        all_digit_pixels.append(seg_pixels)
        overlays.append(overlay)
    # Merge the overlays (assumes they are of the same size)
    combined_overlay = overlays[0].copy()
    for o in overlays[1:]:
        combined_overlay = cv2.addWeighted(combined_overlay, 0.5, o, 0.5, 0)

    recognized_digits = []
    for seg_pixels in all_digit_pixels:
        d = safe_get_number([seg_pixels])
        recognized_digits.append(d)
    # Build reading string: first two digits form the integer part and the third is fractional.
    reading_str = f"{int(recognized_digits[0])}{int(recognized_digits[1])}.{int(recognized_digits[2])}"
    reading = float(reading_str)
    print(f"[DEBUG] Recognized digits: {recognized_digits} -> Reading: {reading_str}")
    return reading, combined_overlay

def main():
    cap = cv2.VideoCapture(0)  # Open the default webcam
    if not cap.isOpened():
        print("[ERROR] Could not open webcam")
        return

    print("Press 'q' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARNING] Failed to capture frame")
            continue

        # Optionally resize frame for performance:
        # frame = cv2.resize(frame, (640, 480))

        # Convert from BGR to RGB for our processing
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process all three digit boxes to get the reading and combined overlay
        reading, overlay = read_digits_from_frame(frame_rgb, digit_boxes, segment_offsets)

        # Draw the reading text onto the overlay
        display_text = f"Reading: {reading:.1f}"
        cv2.putText(overlay, display_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow("Digit Extraction Overlay", overlay)
        print(f"Final reading: {reading:.1f}")

        # Exit if 'q' is pressed.
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
