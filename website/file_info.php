<?php
// Set timezone
date_default_timezone_set('Asia/Manila'); // Adjust this to your desired timezone

// Security Headers
header("Content-Type: application/json; charset=utf-8");
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET");

$file = basename($_GET['file'] ?? ''); // Prevent directory traversal

if (!$file) {
    http_response_code(400); // Bad Request
    echo json_encode(["error" => "No file specified"]);
    exit;
}

$allowedExtensions = ['jpg', 'png', 'gif', 'txt']; // Restrict to specific file types
$fileExtension = pathinfo($file, PATHINFO_EXTENSION);

if (!in_array($fileExtension, $allowedExtensions)) {
    http_response_code(403); // Forbidden
    echo json_encode(["error" => "Invalid file type"]);
    exit;
}

$filePath = __DIR__ . '/' . $file;

if (!file_exists($filePath)) {
    http_response_code(404); // Not Found
    echo json_encode(["error" => "File not found"]);
    exit;
}

try {
    $lastModified = filemtime($filePath); // Get file modification time
    $fileSize = filesize($filePath); // Get file size

    echo json_encode([
        "file" => $file,
        "lastModified" => date("Y-m-d H:i:s", $lastModified), // Human-readable format
        "timestamp" => $lastModified, // UNIX timestamp
        "size" => $fileSize
    ]);
} catch (Exception $e) {
    http_response_code(500); // Internal Server Error
    echo json_encode(["error" => "An error occurred", "details" => $e->getMessage()]);
}
?>