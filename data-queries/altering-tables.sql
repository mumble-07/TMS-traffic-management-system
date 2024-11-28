
-- FIXING ID NUMBER
CREATE TABLE temp_vehicle_detections_rpiC AS
SELECT * FROM u213201264_eenov_sma.vehicle_detections_rpiC;

DELETE FROM u213201264_eenov_sma.vehicle_detections_rpiC;

ALTER TABLE vehicle_detections_rpiC AUTO_INCREMENT = 0;

INSERT INTO u213201264_eenov_sma.vehicle_detections_rpiC (
    vehicle_type, quantity, class_name, confidence, timestamp, x1, y1, x2, y2
)
SELECT
    vehicle_type, quantity, class_name, confidence, timestamp, x1, y1, x2, y2
FROM temp_vehicle_detections_rpiC
ORDER BY timestamp ASC;


-- DELETING IDS
SELECT * FROM u213201264_eenov_sma.vehicle_detections_rpiB;

DELETE FROM vehicle_detections_rpiC
WHERE id BETWEEN 1 AND 1542;

SET SQL_SAFE_UPDATES = 1;