import threading
import subprocess
import sys
from drawing import run


def run_bb_t1():
	"""Run BB-t1.py as a subprocess"""
	subprocess.run([sys.executable, "BB-t1.py"])


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
