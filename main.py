import cv2
import face_recognition
import pickle
import os
import numpy as np
import datetime

encodings_file = 'encodings.pickle'
attendance_file = 'attendance.csv'

# Load the known faces and embeddings
print("[INFO] loading encodings...")
if not os.path.exists(encodings_file):
    print(f"[ERROR] '{encodings_file}' not found. Please run encode_faces.py first.")
    exit()

data = pickle.loads(open(encodings_file, "rb").read())

# Initialize video stream
print("[INFO] starting video stream...")
video_capture = cv2.VideoCapture(0)

def mark_attendance(name):
    if not os.path.exists(attendance_file):
        with open(attendance_file, 'w') as f:
            f.write('Name,Time,Date\n')
            
    with open(attendance_file, 'r+') as f:
        myDataList = f.readlines()
        nameList = []
        for line in myDataList:
            entry = line.split(',')
            nameList.append(entry[0])
            
        if name not in nameList:
            now = datetime.datetime.now()
            dtString = now.strftime('%H:%M:%S')
            dString = now.strftime('%d/%m/%Y')
            f.writelines(f'{name},{dtString},{dString}\n')
            print(f"[ATTENDANCE] Marked for {name}")

while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    # Convert the input frame from BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)

    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(small_frame)
    face_encodings = face_recognition.face_encodings(small_frame, face_locations)

    names = []
    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s)
        matches = face_recognition.compare_faces(data["encodings"], face_encoding)
        name = "Unknown"

        # Or instead, use the known face with the smallest distance to the new face
        face_distances = face_recognition.face_distance(data["encodings"], face_encoding)
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = data["names"][best_match_index]

        names.append(name)
        if name != "Unknown":
            mark_attendance(name)

    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Display the resulting image
    cv2.imshow('Video', frame)

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()
