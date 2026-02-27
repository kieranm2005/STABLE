import threading
import subprocess
import sys
import os
from drawing import run


def run_bb_t1():
	"""Run BB-t1.py as a subprocess"""
	bb_t1_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BB-t1.py")
	subprocess.run([sys.executable, bb_t1_path])


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
