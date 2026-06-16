import face_recognition
image = face_recognition.load_image_file("test_photo.jpg")  # Ensure filename matches!
face_locations = face_recognition.face_locations(image)
print(f"Found {len(face_locations)} face(s)!")