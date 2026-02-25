from __future__ import annotations


class ServoController:
	def __init__(
		self,
		pin_x: int = 6,
		pin_y: int = 5,
		min_angle: float = -45.0,
		max_angle: float = 45.0,
		min_pulse_width: float = 0.0005,
		max_pulse_width: float = 0.0025,
	):
		self.min_angle = float(min_angle)
		self.max_angle = float(max_angle)
		self.pin_x = pin_x
		self.pin_y = pin_y
		self.enabled = False
		self.last_angle_x = 0.0
		self.last_angle_y = 0.0

		self._servo_x = None
		self._servo_y = None

		try:
			from gpiozero import AngularServo

			self._servo_x = AngularServo(
				self.pin_x,
				min_angle=-90,
				max_angle=90,
				min_pulse_width=min_pulse_width,
				max_pulse_width=max_pulse_width,
			)
			self._servo_y = AngularServo(
				self.pin_y,
				min_angle=-90,
				max_angle=90,
				min_pulse_width=min_pulse_width,
				max_pulse_width=max_pulse_width,
			)
			self.enabled = True
		except Exception as exc:
			print(f"[servo_control] Hardware unavailable, using no-op mode: {exc}")

	def _clamp(self, value: float) -> float:
		return max(self.min_angle, min(self.max_angle, value))

	def set_angles(self, angle_x: float, angle_y: float) -> tuple[float, float]:
		a_x = self._clamp(float(angle_x))
		a_y = self._clamp(float(angle_y))
		self.last_angle_x = a_x
		self.last_angle_y = a_y
		if not self.enabled:
			return a_x, a_y
		self._servo_x.angle = a_x
		self._servo_y.angle = a_y
		return a_x, a_y

	def set_by_screen_position(self, x: float, y: float, width: float, height: float) -> tuple[float, float]:
		if width <= 0 or height <= 0:
			return self.last_angle_x, self.last_angle_y

		nx = (float(x) / float(width)) * 2.0 - 1.0
		ny = (float(y) / float(height)) * 2.0 - 1.0

		angle_x = nx * self.max_angle
		angle_y = ny * self.max_angle
		return self.set_angles(angle_x, angle_y)

	def center(self) -> None:
		self.set_angles(0.0, 0.0)

	def close(self) -> None:
		if not self.enabled:
			return
		self._servo_x.detach()
		self._servo_y.detach()
