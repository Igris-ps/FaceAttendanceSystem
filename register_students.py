import os
import face_recognition

def register_students():
    known_encodings = []
    student_data = []  # Stores dictionaries of {name, branch, id}
    
    for filename in os.listdir("registered_faces"):
        if filename.lower().endswith((".jpg", ".png")):
            try:
                # Parse filename (name_branch_id.jpg)
                parts = os.path.splitext(filename)[0].split("_")
                if len(parts) == 3:  # Ensure correct format
                    name, branch, id = parts
                    
                    # Load and encode face
                    image = face_recognition.load_image_file(f"registered_faces/{filename}")
                    encodings = face_recognition.face_encodings(image)
                    
                    if encodings:  # If face detected
                        known_encodings.append(encodings[0])
                        student_data.append({
                            "name": name,
                            "branch": branch,
                            "id": id
                        })
                    else:
                        print(f"⚠️ No face found in {filename}")
                else:
                    print(f"⚠️ Incorrect filename format: {filename} (expected name_branch_id.jpg)")
            except Exception as e:
                print(f"❌ Error processing {filename}: {str(e)}")
    
    return known_encodings, student_data

if __name__ == "__main__":
    encodings, students = register_students()
    print(f"\n✅ Successfully registered {len(students)} students:")
    for student in students:
        print(f"- {student['name']} (Branch: {student['branch']}, ID: {student['id']})")