
import cv2
import os
from picamera2 import Picamera2, Preview
import numpy as np
def main():
	# print("Hello world")
	# print(cv2.__version__)
	# os.system("libcamera-still -o test.jpg")
	# cap = cv2.VideoCapture(0)
	# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
	# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)

	# ret, frame = cap.read()

	picam2 = Picamera2()
	# set frame size to 1920x1080 to maximize image size
	config = picam2.create_video_configuration(main={"size":(2300,2592), "format":"RGB888"})
	picam2.configure(config)
	picam2.set_controls({"AfMode":0, "LensPosition": 5})
	
	
	
	# picam2.start_preview()
	picam2.start()
	print("Hello")
	# center of roi for checking if there is green tape, (y,x) format
	tape_center = [600, 2300/2]
	# size of roi, width in x, height in y
	tape_width = 600
	tape_height = 300
	
	# flag to indicate if a image should be taken 
	# only 1 image should be taken when the camera sees the tape for the first time.
	# take image if flag = 0, do not take image if flag = 1
	tape_flag = 0
	
	
	# center of roi for checking if there is wood on the conveyor belt, (y,x) format
	wood_center = [1700, 2300/2]
	# size of roi, width in x, height in y
	wood_width = 1700
	wood_height = 1700
	
	
	while True:
		# Take image as a numpy array of 640x480 (widthxheight) pixels in rgb format
		frame = picam2.capture_array()
		# print(frame.shape)
		# cv2.imshow("frame", frame)
		# cv2.moveWindow("frame", 0, 0)
		tape_roi = frame[int(tape_center[0]-tape_height/2):int(tape_center[0]+tape_height/2), int(tape_center[1]-tape_width/2):int(tape_center[1]+tape_width/2)]
		# cv2.imshow("tape_roi", tape_roi);
		
		
		wood_roi = frame[int(wood_center[0]-wood_height/2):int(wood_center[0]+wood_height/2), int(wood_center[1]-wood_width/2):int(wood_center[1]+wood_width/2)]
		# cv2.imshow("wood_roi", wood_roi);
		
		# detect if there is more than 75% green tape 
		tape_val = detect_tape(tape_roi)
		wood_val = detect_wood(wood_roi)
		# print(wood_val)
		# print(tape_val)
		if (tape_val > 0.75):
			if ((tape_flag==0) and (wood_val > 0.05)):
				# take image, then set flag to not take image again
				print("Image-Taken")
				cv2.imwrite("test.jpg", wood_roi)
				tape_flag = 1
		# reset flag if more than half of the roi has no green -> tape has moved past already
		elif tape_val < 0.5:
			tape_flag = 0
		
		if (cv2.waitKey(1) == ord("q")):
			break			
			
			
	
	cv2.destroyAllWindows()
	picam2.stop()

# image given in BGR format
# return the percentage of green pixels near the end of the conveyer belt as a float
def detect_tape(img):
	img_hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
	green_mask = cv2.inRange(img_hsv, (41, 60, 80), (72, 255, 255))
	img_hsv = cv2.bitwise_and(img_hsv, img_hsv, mask=green_mask)
	# cv2.imshow("Green Mask", cv2.cvtColor(img_hsv, cv2.COLOR_HSV2RGB))
	return ((np.sum(green_mask)/255)/(green_mask.shape[0]*green_mask.shape[1]))

# image given in BGR format
# returns the percentage of yellowish pixels in the center of the belt where the wood lay
def detect_wood(img):
	img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
	# print(img_hsv)
	yellow_mask = cv2.inRange(img_hsv, (13, 30, 62), (32, 255, 255))
	
	img_hsv = cv2.bitwise_and(img_hsv, img_hsv, mask=yellow_mask)
	# cv2.imshow("Yellow Mask", cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR))
	return ((np.sum(yellow_mask)/255)/(yellow_mask.shape[0]*yellow_mask.shape[1]))

	
if __name__ == "__main__":
	main()



