# Face Recognition Based Attendance System

A Face Recognition Based Attendance System developed using Python, OpenCV, Face Recognition, SQLite, and OpenPyXL.

This project automates the attendance process by recognizing registered student faces through a webcam and recording attendance in real time. The system stores student information securely in a SQLite database and automatically generates Excel attendance reports containing student name, branch, student ID, date, and time.

Key Features:
• Real-time Face Detection and Recognition
• Student Registration using Face Images
• Automatic Attendance Marking
• SQLite Database Integration
• Excel Report Generation (.xlsx)
• Attendance Date and Time Recording
• Duplicate Attendance Prevention
• Unknown Face Detection
• Image Validation and Processing
• Logging and Error Handling
• Secure Storage of Student Records

Technologies Used:
• Python
• OpenCV
• Face Recognition
• SQLite3
• NumPy
• Pillow (PIL)
• OpenPyXL

Project Workflow:
1. Register student images in the registered_faces folder.
2. Generate face encodings from registered images.
3. Store student details and encodings in the database.
4. Capture live video through a webcam.
5. Detect and recognize registered students.
6. Automatically mark attendance.
7. Prevent duplicate attendance entries.
8. Generate Excel attendance reports automatically.

Output:
The system generates Excel attendance reports containing:
• Student Name
• Branch
• Student ID
• Date
• Time