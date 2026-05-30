import face_recognition
import cv2
import os
import numpy as np

FACES_DIR = os.path.join("data", "student_faces")

def load_encodings():
    """Lands images from data/student_faces and returns encodings and names."""
    known_encodings = []
    known_names = []
    
    if not os.path.exists(FACES_DIR):
        os.makedirs(FACES_DIR)
        return known_encodings, known_names

    print("[INFO] Loading encodings...")
    for filename in os.listdir(FACES_DIR):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            name = os.path.splitext(filename)[0]
            path = os.path.join(FACES_DIR, filename)
            
            image = face_recognition.load_image_file(path)
            # Ensure image has faces
            encs = face_recognition.face_encodings(image)
            if encs:
                known_encodings.append(encs[0])
                known_names.append(name)
    
    print(f"[INFO] Loaded {len(known_names)} known faces.")
    return known_encodings, known_names

def recognize_faces(frame, known_encodings, known_names):
    """
    Detects faces in the frame and compares them with known encodings.
    Returns:
        frame_with_boxes: Image with bounding boxes and names.
        recognized_names: List of names recognized in the frame.
    """
    # Resize for speed
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    face_names = []
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        name = "Unknown"
        
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_names[best_match_index]
        
        face_names.append(name)

    # Annotate frame
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4
        
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    return frame, face_names
