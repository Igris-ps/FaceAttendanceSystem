import os
import cv2
import face_recognition
import numpy as np
from datetime import datetime
import sqlite3
from contextlib import contextmanager
from PIL import Image
import logging
from openpyxl import Workbook

# ========================
# Configuration
# ========================
CONFIG = {
    "registered_faces_dir": "registered_faces",
    "database_file": "attendance.db",
    "frame_skip": 3,
    "face_match_threshold": 0.48,  # Lowered threshold for stricter matching
    "min_face_size": (100, 100),
    "output_dir": "attendance_reports"
}

# ========================
# Logging Setup
# ========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('attendance_system.log'),
        logging.StreamHandler()
    ]
)

# ========================
# Database Connection
# ========================
@contextmanager
def db_connection():
    conn = sqlite3.connect(CONFIG['database_file'])
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    try:
        cursor.execute('''CREATE TABLE IF NOT EXISTS students
                         (student_id TEXT PRIMARY KEY,
                          name TEXT,
                          branch TEXT,
                          face_encoding BLOB)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS attendance
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          student_id TEXT,
                          date TEXT,
                          time TEXT,
                          FOREIGN KEY(student_id) REFERENCES students(student_id),
                          UNIQUE(student_id, date))''')
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()

# ========================
# Filename Validation
# ========================
def validate_filename(filename):
    valid_extensions = ('.jpg', '.jpeg', '.png')
    if not filename.lower().endswith(valid_extensions):
        return False
    parts = filename.split('_')
    return len(parts) == 3 and parts[2].split('.')[0].isdigit()

# ========================
# Image Processing
# ========================
def process_image(filepath):
    try:
        with Image.open(filepath) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            if img.size[0] < CONFIG['min_face_size'][0] or img.size[1] < CONFIG['min_face_size'][1]:
                return None, "Image too small"
        image = face_recognition.load_image_file(filepath)
        encodings = face_recognition.face_encodings(image)
        return (encodings[0] if encodings else None, None)
    except Exception as e:
        return None, str(e)

# ========================
# Register Students
# ========================
def register_students():
    if not os.path.exists(CONFIG['registered_faces_dir']):
        os.makedirs(CONFIG['registered_faces_dir'])
        logging.warning(f"Created folder: {CONFIG['registered_faces_dir']}")
        return []

    students = []
    skipped = []

    for file in os.listdir(CONFIG['registered_faces_dir']):
        path = os.path.join(CONFIG['registered_faces_dir'], file)
        if not validate_filename(file):
            skipped.append((file, "Invalid format"))
            continue

        encoding, err = process_image(path)
        if err or encoding is None:
            skipped.append((file, err or "Encoding failed"))
            continue

        name, branch, sid = file.split('_')
        sid = sid.split('.')[0]

        try:
            with db_connection() as cursor:
                cursor.execute(
                    "INSERT OR REPLACE INTO students VALUES (?, ?, ?, ?)",
                    (sid, name, branch, encoding.tobytes())
                )
            students.append({
                "student_id": sid,
                "name": name,
                "branch": branch,
                "encoding": encoding
            })
        except Exception as e:
            skipped.append((file, str(e)))

    if skipped:
        for f, r in skipped:
            logging.warning(f"Skipped {f}: {r}")

    logging.info(f"Registered {len(students)} students.")
    return students

# ========================
# Mark Attendance
# ========================
def mark_attendance(sid):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    with db_connection() as cursor:
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO attendance (student_id, date, time) VALUES (?, ?, ?)",
                (sid, date, time)
            )
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Attendance error: {str(e)}")
            return False

# ========================
# Face Recognition Logic
# ========================
def recognize_faces(frame, known_students):
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    recognized = []
    known_encodings = [student['encoding'] for student in known_students]

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        distances = face_recognition.face_distance(known_encodings, face_encoding)
        best_match_index = np.argmin(distances)

        if distances[best_match_index] < CONFIG['face_match_threshold']:
            student = known_students[best_match_index]
            recognized.append(student['student_id'])

            top, right, bottom, left = [v * 4 for v in (top, right, bottom, left)]
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            label = f"{student['name']} ({student['branch']})"
            cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
        else:
            top, right, bottom, left = [v * 4 for v in (top, right, bottom, left)]
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.putText(frame, "Unknown", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

    return frame, recognized

# ========================
# Excel Report Generation
# ========================
def generate_report(present_ids, students):
    os.makedirs(CONFIG['output_dir'], exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = os.path.join(CONFIG['output_dir'], f"attendance_{timestamp}.xlsx")

    id_map = {s["student_id"]: s for s in students}
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"
    ws.append(["Name", "Branch", "Student ID", "Date", "Time"])

    for sid in present_ids:
        if sid in id_map:
            s = id_map[sid]
            ws.append([s['name'], s['branch'], s['student_id'], date, time])

    wb.save(filepath)
    logging.info(f"✅ Excel saved: {filepath}")

# ========================
# Main Function
# ========================
def main():
    logging.info("🎬 Starting Attendance System")
    registered = register_students()

    with db_connection() as cursor:
        cursor.execute("SELECT student_id, name, branch, face_encoding FROM students")
        db_students = [
            {
                "student_id": row[0],
                "name": row[1],
                "branch": row[2],
                "encoding": np.frombuffer(row[3], dtype=np.float64)
            }
            for row in cursor.fetchall()
        ]

    if not db_students:
        logging.error("🚫 No students found in database.")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Camera not found.")
        return

    seen_today = set()
    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % CONFIG['frame_skip'] != 0:
                continue

            frame, recognized = recognize_faces(frame, db_students)
            for sid in recognized:
                if sid not in seen_today:
                    if mark_attendance(sid):
                        logging.info(f"✔ Marked: {sid}")
                        seen_today.add(sid)

            cv2.imshow("Face Attendance", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        logging.info("🔴 Interrupted")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        generate_report(seen_today, db_students)
        logging.info("🛑 System closed")

if __name__ == "__main__":
    main()
