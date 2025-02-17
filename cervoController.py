#!/usr/bin/env python3
import time

import board
import busio
from adafruit_pca9685 import PCA9685

# -------------------------------
# PCA9685 and Servo Setup
# -------------------------------

# Initialize I2C bus and PCA9685 board
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50  # Standard 50 Hz for servos

# Define servo channels (change channel indices if needed)
servo_horizontal = pca.channels[0]  # Controls horizontal (X-axis) movement
servo_vertical = pca.channels[1]  # Controls vertical (Y-axis) movement

# -------------------------------
# Servo Angle Limits (in degrees)
# -------------------------------
# Define the Field Of View (FOV) in terms of servo angles.
H_MIN = 0  # Leftmost angle for horizontal servo
H_MAX = 180  # Rightmost angle for horizontal servo
V_MIN = 0  # Top angle for vertical servo
V_MAX = 90  # Bottom angle for vertical servo


# -------------------------------
# Function to Set Servo Angle
# -------------------------------
def set_servo_angle(channel, angle):
    """
    Move a servo (attached to a PCA9685 channel) to the given angle.
    Uses pulse widths between 500us (0°) and 2500us (180°).
    """
    min_pulse = 500  # microseconds for 0°
    max_pulse = 2500  # microseconds for 180°
    pulse_us = min_pulse + (max_pulse - min_pulse) * (angle / 180.0)
    # 20,000us is the period for a 50Hz signal. Scale to a 16-bit value:
    duty_cycle = int(pulse_us / 20000 * 0xFFFF)
    channel.duty_cycle = duty_cycle


# -------------------------------
# Grid Scan Configuration
# -------------------------------
# Ask the user for the grid resolution:
n = int(input("Enter the number of horizontal steps (n): "))
p = int(input("Enter the number of vertical steps (p): "))
delay = float(input("Enter the delay (seconds) between steps: "))

# Calculate step sizes (if only one step, step size will be zero)
if n > 1:
    h_step = (H_MAX - H_MIN) / (n - 1)
else:
    h_step = 0  # Stay in one place if n=1

if p > 1:
    v_step = (V_MAX - V_MIN) / (p - 1)
else:
    v_step = 0  # Stay in one place if p=1

print(f"Horizontal step: {h_step:.2f}°, Vertical step: {v_step:.2f}°")

# -------------------------------
# Grid Scanning Loop
# -------------------------------
# Move servos to the starting position
set_servo_angle(servo_horizontal, H_MIN)
set_servo_angle(servo_vertical, V_MIN)
time.sleep(1)  # Allow time for servos to settle

current_v = V_MIN  # Start at the top

try:
    # Loop over each vertical step (row)
    for row in range(p):
        if row % 2 == 0:
            # Even row: left-to-right sweep.
            current_h = H_MIN
            step = h_step
        else:
            # Odd row: right-to-left sweep.
            current_h = H_MAX
            step = -h_step

        # Horizontal sweep for the current row
        for col in range(n):
            # Set servos to current horizontal and vertical angles.
            set_servo_angle(servo_horizontal, current_h)
            set_servo_angle(servo_vertical, current_v)
            print(f"Row {row + 1}/{p}, Col {col + 1}/{n}: "
                  f"Horizontal: {current_h:.1f}°, Vertical: {current_v:.1f}°")
            time.sleep(delay)
            current_h += step

        # Move vertical servo down one step (if not at the last row)
        if row < p - 1:  # Don't move down after the last row
            current_v += v_step

    # Return servos to home position
    print("Returning servos to home position...")
    set_servo_angle(servo_horizontal, H_MIN)
    set_servo_angle(servo_vertical, V_MIN)
    time.sleep(1)

except KeyboardInterrupt:
    print("\nScan interrupted by user.")

finally:
    # Shutdown the PCA9685 and clean up
    pca.deinit()
    print("Scan complete. Exiting now.")
# !/usr/bin/env python3
import time
import board
import busio
from adafruit_pca9685 import PCA9685

# -------------------------------
# PCA9685 and Servo Setup
# -------------------------------

# Initialize I2C bus and PCA9685 board
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50  # Standard 50 Hz for servos

# Define servo channels (change channel indices if needed)
servo_horizontal = pca.channels[0]  # Controls horizontal (X-axis) movement
servo_vertical = pca.channels[1]  # Controls vertical (Y-axis) movement

# -------------------------------
# Servo Angle Limits (in degrees)
# -------------------------------
# Define the Field Of View (FOV) in terms of servo angles.
H_MIN = 0  # Leftmost angle for horizontal servo
H_MAX = 180  # Rightmost angle for horizontal servo
V_MIN = 0  # Top angle for vertical servo
V_MAX = 90  # Bottom angle for vertical servo


# -------------------------------
# Function to Set Servo Angle
# -------------------------------
def set_servo_angle(channel, angle):
    """
    Move a servo (attached to a PCA9685 channel) to the given angle.
    Uses pulse widths between 500us (0°) and 2500us (180°).
    """
    min_pulse = 500  # microseconds for 0°
    max_pulse = 2500  # microseconds for 180°
    pulse_us = min_pulse + (max_pulse - min_pulse) * (angle / 180.0)
    # 20,000us is the period for a 50Hz signal. Scale to a 16-bit value:
    duty_cycle = int(pulse_us / 20000 * 0xFFFF)
    channel.duty_cycle = duty_cycle


# -------------------------------
# Grid Scan Configuration
# -------------------------------
# Ask the user for the grid resolution:
n = int(input("Enter the number of horizontal steps (n): "))
p = int(input("Enter the number of vertical steps (p): "))
delay = float(input("Enter the delay (seconds) between steps: "))

# Calculate step sizes (if only one step, step size will be zero)
if n > 1:
    h_step = (H_MAX - H_MIN) / (n - 1)
else:
    h_step = 0  # Stay in one place if n=1

if p > 1:
    v_step = (V_MAX - V_MIN) / (p - 1)
else:
    v_step = 0  # Stay in one place if p=1

print(f"Horizontal step: {h_step:.2f}°, Vertical step: {v_step:.2f}°")

# -------------------------------
# Grid Scanning Loop
# -------------------------------
# Move servos to the starting position
set_servo_angle(servo_horizontal, H_MIN)
set_servo_angle(servo_vertical, V_MIN)
time.sleep(1)  # Allow time for servos to settle

current_v = V_MIN  # Start at the top

try:
    # Loop over each vertical step (row)
    for row in range(p):
        if row % 2 == 0:
            # Even row: left-to-right sweep.
            current_h = H_MIN
            step = h_step
        else:
            # Odd row: right-to-left sweep.
            current_h = H_MAX
            step = -h_step

        # Horizontal sweep for the current row
        for col in range(n):
            # Set servos to current horizontal and vertical angles.
            set_servo_angle(servo_horizontal, current_h)
            set_servo_angle(servo_vertical, current_v)
            print(f"Row {row + 1}/{p}, Col {col + 1}/{n}: "
                  f"Horizontal: {current_h:.1f}°, Vertical: {current_v:.1f}°")
            time.sleep(delay)
            current_h += step

        # Move vertical servo down one step (if not at the last row)
        if row < p - 1:  # Don't move down after the last row
            current_v += v_step

    # Return servos to home position
    print("Returning servos to home position...")
    set_servo_angle(servo_horizontal, H_MIN)
    set_servo_angle(servo_vertical, V_MIN)
    time.sleep(1)

except KeyboardInterrupt:
    print("\nScan interrupted by user.")

finally:
    # Shutdown the PCA9685 and clean up
    pca.deinit()
    print("Scan complete. Exiting now.")
