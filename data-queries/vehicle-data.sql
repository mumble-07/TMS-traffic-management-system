-- =================== RPI A
SELECT
  *,
  CASE
    WHEN class_name IN ('car') THEN 'Car'
    WHEN class_name IN ('truck', 'bus') THEN 'Truck/Bus'
    WHEN class_name IN ('motorcycle') THEN 'Motorbikes'
    ELSE 'Others'
  END AS Vehicle_Category,
  CASE
    WHEN class_name IN ('car') THEN quantity
    ELSE 0
  END AS car_counter,
  CASE
    WHEN class_name IN ('truck', 'bus') THEN quantity
    ELSE 0
  END AS truck_bus_counter,
  CASE
    WHEN class_name IN ('motorcycle') THEN quantity
    ELSE 0
  END AS motor_count,
  CASE
    WHEN class_name IN ('car', 'truck', 'bus', 'motorcycle') THEN quantity
    ELSE 0
  END AS all_counter
FROM
  u213201264_eenov_sma.vehicle_detections_rpiA;

-- =================== RPI B
FROM
  u213201264_eenov_sma.vehicle_detections_rpiB;

-- =================== RPI C
FROM
  u213201264_eenov_sma.vehicle_detections_rpiC;