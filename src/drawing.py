import time
import json
import os
from dataclasses import dataclass

import pygame


@dataclass
class TrailPoint:
	X: int
	Y: int
	T: float
	DrawFromPrev: bool


def _add_point(trail, x, y, draw_from_prev):
	trail.append(TrailPoint(int(x), int(y), time.monotonic(), draw_from_prev))


def _load_bb_status(status_path):
	try:
		with open(status_path, "r", encoding="utf-8") as file_obj:
			return json.load(file_obj)
	except (FileNotFoundError, json.JSONDecodeError):
		return None


def _build_debug_lines(status):
	now = time.time()
	if not status:
		return ["BB-t1: NO DATA"]

	last_update = status.get("last_update_ts")
	age = now - last_update if isinstance(last_update, (int, float)) else None
	state = str(status.get("state", "unknown")).upper()
	pid = status.get("pid", "?")
	expected = state == "RUNNING" and age is not None and age <= 1.5
	health = "OK" if expected else "NOT OK"

	lines = [f"BB-t1: {state} | Health: {health} | PID: {pid}"]
	if age is not None:
		lines.append(f"Heartbeat age: {age:.2f}s")

	touch_x = status.get("touch_x")
	touch_y = status.get("touch_y")
	if touch_x is not None and touch_y is not None:
		lines.append(f"Touch XY: {touch_x:.1f}, {touch_y:.1f}")

	angle_x = status.get("angle_x")
	angle_y = status.get("angle_y")
	if angle_x is not None and angle_y is not None:
		lines.append(f"Servo Angles XY: {angle_x:.2f}, {angle_y:.2f}")

	err_x = status.get("error_x")
	err_y = status.get("error_y")
	if err_x is not None and err_y is not None:
		lines.append(f"PID Error XY: {err_x:.2f}, {err_y:.2f}")

	output_x = status.get("output_x")
	output_y = status.get("output_y")
	if output_x is not None and output_y is not None:
		lines.append(f"PID Output XY: {output_x:.2f}, {output_y:.2f}")

	error_message = status.get("error")
	if error_message:
		lines.append(f"Error: {error_message}")

	return lines


def run():
	pygame.init()
	screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
	width, height = screen.get_size()

	clock = pygame.time.Clock()
	trail = []
	trail_duration = 2.5
	line_width = 6
	background = (0, 0, 0)
	status_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bb_t1_status.json")
	debug_font = pygame.font.SysFont(None, 28)
	debug_lines = ["BB-t1: NO DATA"]
	last_status_poll = 0.0

	running = True
	while running:
		now = time.monotonic()
		if now - last_status_poll >= 0.1:
			debug_lines = _build_debug_lines(_load_bb_status(status_path))
			last_status_poll = now
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				running = False
			elif event.type == pygame.FINGERDOWN:
				x = event.x * width
				y = event.y * height
				_add_point(trail, x, y, False)
			elif event.type == pygame.FINGERMOTION:
				x = event.x * width
				y = event.y * height
				_add_point(trail, x, y, True)
			elif event.type == pygame.MOUSEBUTTONDOWN:
				x, y = event.pos
				_add_point(trail, x, y, False)
			elif event.type == pygame.MOUSEMOTION:
				if any(event.buttons):
					x, y = event.pos
					_add_point(trail, x, y, True)

		trail = [p for p in trail if now - p.T <= trail_duration]

		screen.fill(background)
		line_surface = pygame.Surface((width, height), pygame.SRCALPHA)

		for i in range(1, len(trail)):
			p0 = trail[i - 1]
			p1 = trail[i]
			if not p1.DrawFromPrev:
				continue
			age = now - p1.T
			alpha = max(0, min(255, int(255 * (1.0 - (age / trail_duration)))))
			color = (255, 255, 255, alpha)
			pygame.draw.line(line_surface, color, (p0.X, p0.Y), (p1.X, p1.Y), line_width)

		screen.blit(line_surface, (0, 0))
		text_y = 12
		for line in debug_lines:
			text_surface = debug_font.render(line, True, (0, 255, 0))
			screen.blit(text_surface, (12, text_y))
			text_y += 26
		pygame.display.flip()
		clock.tick(60)

	pygame.quit()


def main():
	run()


if __name__ == "__main__":
	main()
