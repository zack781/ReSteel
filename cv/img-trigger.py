import cv2
import signal
import sys
import signal
import imutils

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
        ret, frame = cap.read()
        frame = imutils.resize(frame, width=WIDTH)
        success, buffer = cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,50])

        height, width, _ = frame.shape

        # x_critical =

        for x in range(0, width):
            for y in range(0, height):
                # frame[y, x] = (255, 255, 255)
                print(frame[y, x])

        if success:
            cv2.imwrite('img.jpg', frame)
            print('Image captured')
        else:
            print('Error capturing image')
        # flag = True


