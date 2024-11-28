import cv2
import numpy as np

# Create a simple black image with text
test_image = np.zeros((640, 640, 3), dtype=np.uint8)
cv2.putText(test_image, "Test Image", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3, cv2.LINE_AA)

# Display the test image
cv2.imshow("Test Window", test_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
