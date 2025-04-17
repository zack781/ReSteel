import cv2
import signal
import sys
import signal
import imutils
import os
from picamera2 import Picamera2, Preview

WIDTH = 640

cap = cv2.VideoCapture(0)

def signal_handler(sig, frame):
    cap.release()
    print('Exiting...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

flag = False
while True:
    if (flag == False):
        # frame = cv2.imread("/Users/zack/Downloads/square.png")
        picam2 = Picamera2()
        picam2.start()
        frame = picam2.capture_array()
        # frame = imutils.resize(frame, width=WIDTH) # Resize frame while maintaining aspect ratio
        success, buffer = cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,50])

        # height, width, _ = frame.shape

        # green_pixels = 0
        # x_critical = 640 * 0.75
        # test_count = 0
        # for x in range(0, width):
        #     for y in range(0, height):
        #         test_count += 1

        #         print("color = ", frame[y, x])
        #         if (frame[y, x][1] > 200 and frame[y, x][0] < 50 and frame[y, x][2] < 50):
        #             green_pixels += 1
        #             break

        # if (green_pixels / ((width - x_critical) * height) == 1):
        #     # flag = True
        #     print('Green detected')

        if success:
            print("writing image to file")
            cv2.imwrite('img1.jpg', frame)
        else:
            print('Error capturing image')
        flag = True
