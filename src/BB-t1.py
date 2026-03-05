import atexit
import json
import os
import time

import evdev
from evdev import InputDevice, ecodes
from gpiozero import AngularServo

# --- CONFIGURATION ---
# GPIO Pins (BCM Numbering)
PIN_SERVO_Y = 5 #BLUE
PIN_SERVO_X = 6 #GREEN

# Servo Settings (Adjust min/max pulse width for your specific servos)
# Standard servos usually have a pulse width range of 0.001 to 0.002 seconds
SERVO_MIN_PULSE = 0.0005
SERVO_MAX_PULSE = 0.0025

# PID Constants (These MUST be tuned for your specific hardware mechanics)
# Start with Kp, leave Ki and Kd at 0, then tune.
KP = 0.005 # Proportional
KI = 0.00  # Integral
KD = 0.001  # Derivative

# Screen Resolution (Waveshare 7 inch is typically 1024x600 or 800x480)
# You can find this by running 'evtest'
SCREEN_WIDTH_MAX = 3975
SCREEN_HEIGHT_MAX = 3650

# Setpoint (The center of the screen where we want the ball)
SETPOINT_X = SCREEN_WIDTH_MAX / 2
SETPOINT_Y = SCREEN_HEIGHT_MAX / 2

# --- PID CONTROLLER CLASS ---
class PID:
    def __init__(self, kp, ki, kd, setpoint):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.last_error = 0
        self.integral = 0
        self.last_time = time.time()

    def compute(self, current_value):
        current_time = time.time()
        dt = current_time - self.last_time
        
        # Calculate Error
        error = self.setpoint - current_value
        
        # Proportional Term
        P = self.kp * error
        
        # Integral Term (accumulate error over time)
        self.integral += error * dt
        # Clamp integral to prevent "windup" (optional but recommended)
        self.integral = max(min(self.integral, 50), -50)
        I = self.ki * self.integral
        
        # Derivative Term (rate of change of error)
        if dt > 0:
            D = self.kd * ((error - self.last_error) / dt)
        else:
            D = 0
            
        # Store state for next loop
        self.last_error = error
        self.last_time = current_time
        
        # Return total correction
        return P + I + D


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(BASE_DIR, "bb_t1_status.json")


def _write_status(update):
    status = {}
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as file_obj:
            status = json.load(file_obj)
    except (FileNotFoundError, json.JSONDecodeError):
        status = {}

    status.update(update)
    status["last_update_ts"] = time.time()

    temp_path = STATUS_FILE + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as file_obj:
        json.dump(status, file_obj)
    os.replace(temp_path, STATUS_FILE)


def _mark_stopped():
    _write_status({"process_alive": False, "state": "stopped"})

# --- HARDWARE SETUP ---
print("Initializing Servos...")
# Initializing with initial_angle=0 (assumed flat)
servo_x = AngularServo(PIN_SERVO_X, min_angle=-90, max_angle=90, 
                       min_pulse_width=SERVO_MIN_PULSE, max_pulse_width=SERVO_MAX_PULSE)
servo_y = AngularServo(PIN_SERVO_Y, min_angle=90, max_angle=-90,
                       min_pulse_width=SERVO_MIN_PULSE, max_pulse_width=SERVO_MAX_PULSE)

# --- INPUT DEVICE SETUP ---
# You need to find which event path corresponds to your touchscreen.
# Run 'ls /dev/input/by-id/' or use the function below to try to auto-detect.
device_path = None
try:
    # This is a common name for Waveshare touch interfaces, but it varies!
    # You might need to change 'event0', 'event1', etc. manually.
    # A safe bet is to look for "Touchscreen" in the name.
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        print(f"Detected device: {device.path} - {device.name}")
        if "touch" in device.name.lower():
            device_path = device.path
            print(f"Auto-selected Touchscreen: {device.path}")
            break
            
    if not device_path:
        # Fallback: asking user or defaulting to event0
        device_path = '/dev/input/event0'
        print(f"No device with 'touch' in name found. Defaulting to {device_path}")

    touchscreen = InputDevice(device_path)
except Exception as e:
    print(f"Error finding touchscreen: {e}")
    _write_status(
        {
            "process_alive": False,
            "state": "error",
            "error": f"touchscreen init failed: {e}",
        }
    )
    exit()

# Initialize PID Controllers
pid_x = PID(KP, KI, KD, SETPOINT_X)
pid_y = PID(KP, KI, KD, SETPOINT_Y)

print("Starting Control Loop. Press Ctrl+C to stop.")

_write_status(
    {
        "process_alive": True,
        "state": "starting",
        "pid": os.getpid(),
        "device_path": device_path,
        "setpoint_x": SETPOINT_X,
        "setpoint_y": SETPOINT_Y,
        "kp": KP,
        "ki": KI,
        "kd": KD,
    }
)
atexit.register(_mark_stopped)

# Current ball position (initialized to center to avoid jump start)
current_x = SETPOINT_X
current_y = SETPOINT_Y
last_status_write = 0.0

try:
    # We use read_loop() to block until data comes in. 
    # NOTE: If the ball stops touching the screen, the loop pauses. 
    # For a real-time system, we might need a non-blocking loop, 
    # but 'read_loop' is the most responsive method for 'evdev'.
    
    for event in touchscreen.read_loop():
        if event.type == ecodes.EV_ABS:
            if event.code == ecodes.ABS_X:
                current_x = event.value
            elif event.code == ecodes.ABS_Y:
                current_y = event.value
                
            # Perform PID Calculation
            # The output is the Angle adjustment needed
            output_x = pid_x.compute(current_x)
            output_y = pid_y.compute(current_y)
            
            # Map PID output to Servo Angles (-90 to 90)
            # We invert the X output because if the ball is on the right (+X),
            # we need to lift the right side (Positive Angle) to roll it back left.
            # You may need to flip the +/- signs depending on your physical linkage.
            
            angle_x = -output_x
            angle_y = -output_y
            
            # Clamp angles to safe servo limits (e.g., -45 to 45 degrees)
            # Most balance tables don't need full 90 degree tilt.
            angle_x = max(min(angle_x, 45), -45)
            angle_y = max(min(angle_y, 45), -45)
            
            # Update Servos
            servo_x.angle = angle_x
            servo_y.angle = angle_y

            now = time.time()
            if now - last_status_write >= 0.1:
                _write_status(
                    {
                        "process_alive": True,
                        "state": "running",
                        "touch_x": current_x,
                        "touch_y": current_y,
                        "error_x": pid_x.last_error,
                        "error_y": pid_y.last_error,
                        "output_x": output_x,
                        "output_y": output_y,
                        "angle_x": angle_x,
                        "angle_y": angle_y,
                    }
                )
                last_status_write = now
            
            # Debugging (Uncomment to tune)
            # print(f"X: {current_x} | Err: {pid_x.last_error:.1f} | Out: {angle_x:.1f}")

except KeyboardInterrupt:
    print("\nStopping...")
except Exception as e:
    _write_status(
        {
            "process_alive": False,
            "state": "error",
            "error": f"control loop failed: {e}",
        }
    )
    raise
finally:
    servo_x.detach()

    servo_y.detach()




