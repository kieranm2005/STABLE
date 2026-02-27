import threading
import subprocess
import sys
import os
import json
import time
from drawing import run


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


def run_bb_t1():
	"""Run BB-t1.py as a subprocess"""
	bb_t1_path = os.path.join(BASE_DIR, "BB-t1.py")
	_write_status({
		"process_alive": False,
		"state": "launching",
		"error": None,
		"launcher_pid": os.getpid(),
	})

	try:
		result = subprocess.run(
			[sys.executable, bb_t1_path],
			capture_output=True,
			text=True,
		)
		if result.returncode != 0:
			stderr_tail = (result.stderr or "").strip().splitlines()[-1:] or ["unknown error"]
			_write_status(
				{
					"process_alive": False,
					"state": "error",
					"error": f"BB-t1 exited ({result.returncode}): {stderr_tail[0]}",
				}
			)
		else:
			_write_status(
				{
					"process_alive": False,
					"state": "stopped",
					"error": None,
				}
			)
	except Exception as exc:
		_write_status(
			{
				"process_alive": False,
				"state": "error",
				"error": f"launcher failed: {exc}",
			}
		)


def main():
	# Create threads for concurrent execution
	drawing_thread = threading.Thread(target=run, name="DrawingThread")
	bb_t1_thread = threading.Thread(target=run_bb_t1, name="BB-t1Thread")
	
	# Start both threads
	drawing_thread.start()
	bb_t1_thread.start()
	
	# Wait for both threads to complete
	drawing_thread.join()
	bb_t1_thread.join()


if __name__ == "__main__":
	main()
