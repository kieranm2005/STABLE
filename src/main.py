import threading
from drawing import run
from servo_control import ServoController


def run_drawing(servo_controller):
	def on_touch(x, y, width, height):
		angle_x, angle_y = servo_controller.set_by_screen_position(x, y, width, height)
		return {
			"x": x,
			"y": y,
			"angle_x": angle_x,
			"angle_y": angle_y,
			"hardware_enabled": servo_controller.enabled,
		}

	run(on_touch=on_touch)


def main():
	servo_controller = ServoController()
	servo_controller.center()

	try:
		# Drawing loop blocks until exit (ESC or window close)
		drawing_thread = threading.Thread(
			target=run_drawing,
			args=(servo_controller,),
			name="DrawingThread",
		)
		drawing_thread.start()
		drawing_thread.join()
	finally:
		servo_controller.center()
		servo_controller.close()


if __name__ == "__main__":
	main()
