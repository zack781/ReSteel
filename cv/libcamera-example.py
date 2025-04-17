
import cv2
import os
from picamera2 import Picamera2, Preview

def main():
	# print("Hello world")
	# print(cv2.__version__)
	os.system("libcamera-still -o test.jpg")
	# cap = cv2.VideoCapture(0)
	# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
	# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)

	# ret, frame = cap.read()

	picam2 = Picamera2()
	# picam2.start_preview()
	picam2.start()
	frame = picam2.capture_array()
	print(frame.shape)
	cv2.imshow("frame", frame)
	cv2.waitKey(0);

	picam2.stop()

if __name__ == "__main__":
	main()
