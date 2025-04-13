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
        print("Start Frame Capture")
        # ret, frame = cap.read()
        frame = cv2.imread("/Users/zack/Downloads/square.png")
        frame = imutils.resize(frame, width=WIDTH) # Resize frame while maintaining aspect ratio
        success, buffer = cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,50])

        height, width, _ = frame.shape
        print("width = ", width)
        print("height = ", height)

        green_pixels = 0
        x_critical = 640 * 0.75
        test_count = 0
        for x in range(0, width):
            for y in range(0, height):
                test_count += 1
                
                print("color = ", frame[y, x])
                if (frame[y, x][1] > 200 and frame[y, x][0] < 50 and frame[y, x][2] < 50):
                    green_pixels += 1
                    break

        print("test_count = ", test_count)
        print("green_pixels = ", green_pixels)
        print("area = ", (width - x_critical) * height)
        print("green_pixels / ((width - x_critical) * height) = ", green_pixels / ((width - x_critical) * height))
        if (green_pixels / ((width - x_critical) * height) == 1):
            # flag = True
            print('Green detected')

        if success:
            cv2.imwrite('img.jpg', frame)
        else:
            print('Error capturing image')
        flag = True
