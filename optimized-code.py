import cv2
import numpy as np
import mysql.connector
from mysql.connector import Error
from picamera2 import Picamera2
from ultralytics import YOLO
from ftplib import FTP
from datetime import datetime, timedelta, timezone

# FTP Configuration
ftp_host = 'ftp.sanmarcelinoayala.com'
ftp_user = 'u213201264.admin'
ftp_pass = 'SanMarcelinoAyala1!'

local_file = 'rpiA.jpg'
remote_file = 'rpiA.jpg'

# Initialize the camera and model
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 360)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.controls.FrameRate = 30
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

model = YOLO("yolo11n.pt")  # Replace with your YOLO model

# Define thresholds
CONFIDENCE_THRESHOLD = 0.5
TIME_THRESHOLD = timedelta(seconds=5)
IOU_THRESHOLD = 0.5

# Philippine timezone
philippine_time = timezone(timedelta(hours=8))

# Keep track of last detections
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

def upload_to_ftp(local_path, remote_path):
    """Upload a file to the FTP server."""
    try:
        with FTP(ftp_host) as ftp:
            ftp.login(user=ftp_user, passwd=ftp_pass)
            with open(local_path, 'rb') as file:
                ftp.storbinary(f'STOR {remote_path}', file)
            print(f"File uploaded to {remote_path}")
    except Exception as e:
        print(f"Failed to upload file: {e}")

def initialize_database():
    """Initialize the MySQL database connection and create table if not exists."""
    try:
        db_connection = mysql.connector.connect(
            host="153.92.15.35",
            user="u213201264_root_eenov_sma",
            password="EEnov_sma_DB@2024",
            database="u213201264_eenov_sma"
        )
        cursor = db_connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_detections_rpiA (
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
        """)
        db_connection.commit()
        print("Database initialized.")
        return db_connection, cursor
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None, None

def insert_detection(cursor, db_connection, class_name, confidence, current_time, x1, y1, x2, y2, vehicle_count):
    """Insert unique vehicle detection into the database."""
    try:
        # Avoid duplicates
        check_query = """
            SELECT id FROM vehicle_detections_rpiA
            WHERE class_name = %s AND ABS(TIMESTAMPDIFF(SECOND, timestamp, %s)) < 5
            AND x1 BETWEEN %s - 10 AND %s + 10
            AND y1 BETWEEN %s - 10 AND %s + 10
            AND x2 BETWEEN %s - 10 AND %s + 10
            AND y2 BETWEEN %s - 10 AND %s + 10
        """
        cursor.execute(check_query, (class_name, current_time, x1, x1, y1, y1, x2, x2, y2, y2))
        if cursor.fetchone():
            print(f"Duplicate detection for {class_name} skipped.")
            return

        # Insert unique detection
        insert_query = """
            INSERT INTO vehicle_detections_rpiA (vehicle_type, quantity, class_name, confidence, timestamp, x1, y1, x2, y2)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (class_name, vehicle_count, class_name, confidence, current_time, x1, y1, x2, y2))
        db_connection.commit()
        print(f"Inserted {class_name} detection into the database.")
    except Error as e:
        print(f"Failed to insert detection: {e}")

def main():
    # Initialize database
    db_connection, cursor = initialize_database()
    if not db_connection or not cursor:
        print("Database connection failed. Exiting.")
        return

    try:
        while True:
            frame = picam2.capture_array()
            results = model(frame)
            vehicle_count = {}

            for detection in results[0].boxes:
                class_id = int(detection.cls[0])
                class_name = model.names[class_id]

                if class_name != "car":  # Save only car detections
                    continue

                x1, y1, x2, y2 = map(lambda x: int(x.item()), detection.xyxy[0])
                confidence = float(detection.conf[0].item())
                if confidence < CONFIDENCE_THRESHOLD:
                    continue

                current_time = datetime.now(philippine_time)

                if class_name in last_detections:
                    last_time, last_box = last_detections[class_name]
                    if (current_time - last_time) < TIME_THRESHOLD and calculate_iou((x1, y1, x2, y2), last_box) > IOU_THRESHOLD:
                        continue

                last_detections[class_name] = (current_time, (x1, y1, x2, y2))
                vehicle_count[class_name] = vehicle_count.get(class_name, 0) + 1
                insert_detection(cursor, db_connection, class_name, confidence, current_time, x1, y1, x2, y2, vehicle_count[class_name])

            cv2.imwrite(local_file, frame)
            upload_to_ftp(local_file, remote_file)
            print("Frame processed.")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        if cursor:
            cursor.close()
        if db_connection:
            db_connection.close()
        cv2.destroyAllWindows()
        picam2.close()

if __name__ == "__main__":
    main()