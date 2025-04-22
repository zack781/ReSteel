import cv2
import signal
import sys
import signal
import imutils
import os
import numpy as np

WIDTH = 640

cap = cv2.VideoCapture(0)

def signal_handler(sig, frame):
    cap.release()
    print('Exiting...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

flag = False
# picam2 = Picamera2()
# picam2.start()

while True:
    if (flag == False):
        frame = cv2.imread("square.png")
        # img = picam2.capture_array()
        img = imutils.resize(frame, width=WIDTH) # Resize frame while maintaining aspect ratio
        success, buffer = cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,50])

        height, width, _ = img.shape
        print("height = ", height)
        print("width = ", width)

        # center = [height/2, width * 0.875]

        # roi = img[int(center[0]-height/2):int(center[0]+height/2), int(center[1]-10):int(center[1]+10)]
        # img = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # green_mask = cv2.inRange(img, (41, 85, 102), (72, 255, 255))
        # output = cv2.bitwise_and(img, img, mask = green_mask)

        # # cv2.imshow("Final Output", output)
        # # cv2.waitKey(0)

        # print ("percentage = ",  (np.sum(green_mask)/255)/(np.shape(img)[0]*np.shape(img)[1]))
        # if ((np.sum(green_mask)/255)/(np.shape(img)[0]*np.shape(img)[1]) > 0.75):
        #     print("Green Tape Detected")

        green_pixels = 0
        x_critical = 640 * 0.75
        test_count = 0
        for x in range(0, width):
            for y in range(0, height):
                test_count += 1

                # print(x, " - ", y,  " = ", frame[y, x])
                if (x >= x_critical):
                     green_pixels += 1

        print("test_count = ", test_count)
        print("green_pixels = ", green_pixels)
        if (green_pixels / ((width - x_critical) * height) == 1):
            # flag = True
            print('Green detected')

        if success:
            print("writing image to file")
            cv2.imwrite('img1.jpg', frame)
        else:
            print('Error capturing image')
        flag = True
