import time
import importlib

PIN_SERVO_Y = 5
PIN_SERVO_X = 6
SERVO_MIN_PULSE = 0.0005
SERVO_MAX_PULSE = 0.0025

KP = 0.06
KI = 0.04
KD = 0.01

SCREEN_WIDTH_MAX = 3975
SCREEN_HEIGHT_MAX = 3650
SETPOINT_X = SCREEN_WIDTH_MAX / 2
SETPOINT_Y = SCREEN_HEIGHT_MAX / 2


class PID:
    def __init__(self, kp, ki, kd, setpoint):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.last_error = 0.0
        self.integral = 0.0
        self.last_time = time.time()

    def compute(self, current_value):
        current_time = time.time()
        dt = current_time - self.last_time

        error = self.setpoint - current_value
        p_term = self.kp * error

        self.integral += error * dt
        self.integral = max(min(self.integral, 50.0), -50.0)
        i_term = self.ki * self.integral

        d_term = 0.0
        if dt > 0:
            d_term = self.kd * ((error - self.last_error) / dt)

        self.last_error = error
        self.last_time = current_time

        return p_term + i_term + d_term


def find_touchscreen_device(preferred_path="/dev/input/event2"):
    try:
        evdev = importlib.import_module("evdev")
    except Exception as exc:
        raise RuntimeError(f"evdev not available: {exc}") from exc

    device_path = preferred_path
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

    for device in devices:
        print(f"Detected device: {device.path} - {device.name}")
        if "touch" in device.name.lower():
            device_path = device.path
            print(f"Auto-selected Touchscreen: {device_path}")
            break

    return device_path


def main():
    try:
        gpiozero = importlib.import_module("gpiozero")
        evdev = importlib.import_module("evdev")
        AngularServo = getattr(gpiozero, "AngularServo")
        InputDevice = getattr(evdev, "InputDevice")
        ecodes = getattr(evdev, "ecodes")
    except Exception as exc:
        raise RuntimeError(f"Missing runtime dependency: {exc}") from exc

    print("Initializing Servos...")
    servo_x = AngularServo(
        PIN_SERVO_X,
        min_angle=-90,
        max_angle=90,
        min_pulse_width=SERVO_MIN_PULSE,
        max_pulse_width=SERVO_MAX_PULSE,
    )
    servo_y = AngularServo(
        PIN_SERVO_Y,
        min_angle=-90,
        max_angle=90,
        min_pulse_width=SERVO_MIN_PULSE,
        max_pulse_width=SERVO_MAX_PULSE,
    )

    device_path = find_touchscreen_device()
    touchscreen = InputDevice(device_path)

    pid_x = PID(KP, KI, KD, SETPOINT_X)
    pid_y = PID(KP, KI, KD, SETPOINT_Y)

    print("Starting Control Loop. Press Ctrl+C to stop.")

    current_x = SETPOINT_X
    current_y = SETPOINT_Y

    try:
        for event in touchscreen.read_loop():
            if event.type != ecodes.EV_ABS:
                continue

            if event.code == ecodes.ABS_X:
                current_x = event.value
            elif event.code == ecodes.ABS_Y:
                current_y = event.value
            else:
                continue

            output_x = pid_x.compute(current_x)
            output_y = pid_y.compute(current_y)

            angle_x = max(min(-output_x, 45), -45)
            angle_y = max(min(-output_y, 45), -45)

            servo_x.angle = angle_x
            servo_y.angle = angle_y

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        servo_x.detach()
        servo_y.detach()


if __name__ == "__main__":
    main()
