import sys

# Add the path to `ultralytics` from your virtual environment
sys.path.insert(0, "/home/eenov/yolov5/venv/lib/python3.11/site-packages")

from picamera2 import Picamera2
import cv2
import numpy as np
#from ultralytics import YOLO


# Set up the camera with Picamera2
picam2 = Picamera2()

picam2.start()

# Load YOLO model
#model = YOLO("yolov5s.pt")

while True:
    # Run YOLO model on the captured frame
    #results = model(frame)
    
    frame = picam2.capture_array()
    if frame is not None:
        print(f"Captured frame with shape: {frame.shape}")

        # Convert frame from RGB to BGR for OpenCV
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

        # Display the frame
        cv2.imshow("Camera Feed", frame_bgr)

        # Add a break condition
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

picam2.close()
cv2.destroyAllWindows()

