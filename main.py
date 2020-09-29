import face_recognition
from datetime import datetime

known_image = face_recognition.load_image_file("test_assets/obama.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]

print(datetime.now())
unknown_image = face_recognition.load_image_file("test_assets/obama2.jpg")
unknown_encoding = face_recognition.face_encodings(unknown_image)[0]
print(datetime.now())

results = face_recognition.compare_faces([known_encoding], unknown_encoding)

print(results)