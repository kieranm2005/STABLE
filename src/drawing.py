import time
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


def run():
	pygame.init()
	pygame.display.set_caption("Touch Trail")

	screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
	width, height = screen.get_size()

	clock = pygame.time.Clock()
	trail = []
	trail_duration = 2.5
	line_width = 6
	background = (0, 0, 0)

	running = True
	while running:
		now = time.monotonic()
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
		pygame.display.flip()
		clock.tick(60)

	pygame.quit()


def main():
	run()


if __name__ == "__main__":
	main()
