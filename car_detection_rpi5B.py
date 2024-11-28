import cv2
import numpy as np
import mysql.connector
from mysql.connector import Error
from picamera2 import Picamera2
from ultralytics import YOLO
from ftplib import FTP
from datetime import datetime, timedelta, timezone

# FTP Configuration
ftp_host = 'ftp.sanmarcelinoayala.com'  # Replace with your FTP host
ftp_user = 'u213201264.admin'           # Replace with your FTP username
ftp_pass = 'SanMarcelinoAyala1!'        # Replace with your FTP password

local_file = 'rpiB.jpg'                  # Local file path for the saved image
remote_file = 'rpiB.jpg'                 # Remote path on the FTP server

# Initialize the camera and model
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 360)  # Lower resolution to increase speed
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.controls.FrameRate = 30  # Adjust FPS as needed
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

model = YOLO("yolo11n.pt")  # Replace with your YOLO v11 model

# Define vehicle class IDs (based on your model's class list)
vehicle_class_ids = [2, 3, 5, 7]  # Example for car, truck, bus, motorcycle

# Define thresholds for duplicate detection
CONFIDENCE_THRESHOLD = 0.5
TIME_THRESHOLD = timedelta(seconds=5)
IOU_THRESHOLD = 0.5

# Dictionary to store last detection time and bounding box for each vehicle type
last_detections = {}

def calculate_iou(box1, box2):
    """Calculate Intersection over Union (IoU) for bounding boxes."""
    x1, y1, x2, y2 = box1
    x1_p, y1_p, x2_p, y2_p = box2

    inter_x1 = max(x1, x1_p)
    inter_y1 = max(y1, y1_p)
    inter_x2 = min(x2, x2_p)
    inter_y2 = min(y2, y2_p)

    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    if inter_area == 0:
        return 0.0

    box1_area = (x2 - x1) * (y2 - y1)
    box2_area = (x2_p - x1_p) * (y2_p - y1_p)
    iou = inter_area / float(box1_area + box2_area - inter_area)
    return iou

# Define Philippine timezone
philippine_time = timezone(timedelta(hours=8))

def upload_to_ftp(local_path, remote_path):
    """Upload a file to the FTP server, creating directories if needed."""
    try:
        with FTP(ftp_host) as ftp:
            ftp.login(user=ftp_user, passwd=ftp_pass)
            # Navigate to the directory or create it if it doesn't exist
            remote_dir = '/'.join(remote_path.split('/')[:-1])  # Extract the directory path
            if remote_dir:
                try:
                    ftp.cwd(remote_dir)  # Try changing to the directory
                except Exception:
                    # If directory doesn't exist, create it
                    print(f"Directory {remote_dir} does not exist. Creating it.")
                    dirs = remote_dir.split('/')
                    current_dir = ''
                    for dir in dirs:
                        current_dir = f"{current_dir}/{dir}" if current_dir else dir
                        try:
                            ftp.cwd(current_dir)
                        except Exception:
                            ftp.mkd(current_dir)  # Create the directory
                            ftp.cwd(current_dir)  # Change to the newly created directory

            # Upload the file
            with open(local_path, 'rb') as file:
                ftp.storbinary(f'STOR {remote_path.split("/")[-1]}', file)
            print(f"File uploaded successfully to {remote_path}")
    except Exception as e:
        print(f"Failed to upload file: {e}")

def initialize_database():
    """Initialize the MySQL database connection and create table if not exists."""
    try:
        # Connect to MySQL database
        db_connection = mysql.connector.connect(
            host="153.92.15.35",
            user="u213201264_root_eenov_sma",
            password="EEnov_sma_DB@2024",
            database="u213201264_eenov_sma"
        )
        cursor = db_connection.cursor()

        # Create table if it does not exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS vehicle_detections_rpiB (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vehicle_type VARCHAR(50),
            quantity INT,
            class_name VARCHAR(50),
            confidence FLOAT,
            timestamp TIMESTAMP,
            x1 INT,
            y1 INT,
            x2 INT,
            y2 INT
        )
        """
        cursor.execute(create_table_query)
        db_connection.commit()
        print("Database initialized and table ensured.")
        return db_connection, cursor
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None, None

def insert_detection(cursor, db_connection, class_name, confidence, current_time, x1, y1, x2, y2, vehicle_count):
    """Insert a unique vehicle detection into the database."""
    try:
        insert_query = """
            INSERT INTO vehicle_detections_rpiB (vehicle_type, quantity, class_name, confidence, timestamp, x1, y1, x2, y2)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (class_name, vehicle_count, class_name, confidence, current_time, x1, y1, x2, y2))
        db_connection.commit()
        print(f"Inserted {class_name} detection into the database.")
    except Error as e:
        print(f"Failed to insert detection into database: {e}")

def main():
    # Initialize database
    db_connection, cursor = initialize_database()
    if not db_connection or not cursor:
        print("Database connection failed. Exiting.")
        return

    try:
        while True:
            # Capture a frame
            frame = picam2.capture_array()

            # Convert frame to RGB if it has an alpha channel
            if frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)

            # Run YOLO model inference on the frame
            results = model(frame)

            # Filter detections to only include vehicles
            annotated_frame = frame.copy()
            vehicle_count = {}

            for detection in results[0].boxes:
                class_id = int(detection.cls[0])

                if class_id in vehicle_class_ids:
                    x1, y1, x2, y2 = map(lambda x: int(x.item()), detection.xyxy[0])
                    confidence = float(detection.conf[0].item())
                    class_name = model.names[class_id]
                    
                    if confidence < CONFIDENCE_THRESHOLD:
                        continue

                    # Get current timestamp in Philippine time
                    current_time = datetime.now(philippine_time)

                    # Check for duplicates based on spatial and temporal proximity
                    if class_name in last_detections:
                        last_time, last_box = last_detections[class_name]
                        time_diff = current_time - last_time
                        iou = calculate_iou((x1, y1, x2, y2), last_box)
                        
                        if time_diff < TIME_THRESHOLD and iou > IOU_THRESHOLD:
                            continue

                    # Update last detection record for the vehicle type
                    last_detections[class_name] = (current_time, (x1, y1, x2, y2))

                    # Increment vehicle count by type
                    if class_name in vehicle_count:
                        vehicle_count[class_name] += 1
                    else:
                        vehicle_count[class_name] = 1

                    # Insert unique detection into the database
                    insert_detection(cursor, db_connection, class_name, confidence, current_time, x1, y1, x2, y2, vehicle_count[class_name])

                    # Log detected vehicle with timestamp
                    timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{timestamp}] Detected {class_name} with confidence {confidence:.2f} at location ({x1}, {y1}, {x2}, {y2})")

                    # Draw bounding box and label on the annotated frame
                    label = f"{class_name} {confidence:.2f}"
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(annotated_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # Save the current frame as a JPEG image
            cv2.imwrite(local_file, annotated_frame)
            print(f"Image saved as {local_file}")

            # Upload the image to the FTP server
            upload_to_ftp(local_file, remote_file)

            # Display the annotated frame
            cv2.imshow("Camera - Vehicle Detection", annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Error as e:
        print(f"MySQL Error: {e}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    finally:
        # Close database connection
        if cursor:
            cursor.close()
        if db_connection:
            db_connection.close()
            print("Database connection closed.")
        
        # Release resources
        cv2.destroyAllWindows()
        picam2.close()

if __name__ == "__main__":
    main()
