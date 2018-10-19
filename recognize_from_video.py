# -*- coding: UTF-8 -*-
import face_recognition
import cv2
import os
import numpy as np


# Encoding file folder
encoding_file = "./encoding_files"
# Load font
ft = ft2.put_chinese_text('Deng.ttf')
# Video Capture
video_capture = cv2.VideoCapture(0)
# Encoding dictionary
encoding_dic = {}

# Read encodings from file
for file in os.listdir(encoding_file):
    name = file[:(len(file) - 4)]
    encoding = np.fromfile(encoding_file + "/" + file, dtype=np.float64).tolist()
    encoding_dic[name] = encoding

while True:
    # Get one frame
    ret, frame = video_capture.read()
    # Get face encodings in one frame
    face_locations_in_frame = face_recognition.face_locations(frame)
    face_encodings_in_frame = face_recognition.face_encodings(frame, face_locations_in_frame)
    # Recognize each face in one frame
    for (top, right, bottom, left), face_encoding in zip(face_locations_in_frame, face_encodings_in_frame):
        name = "Unknown"
        # Compare each encoding in face set
        for k, v in encoding_dic.items():
            # results is an array of True/False telling if the unknown face matched anyone in the known_faces array
            match = face_recognition.compare_faces([v], face_encoding, tolerance=0.35)
            if match[0]:
                name = k
                break
        # Mark name on frame
        cv2.rectangle(frame, (left, top), (right, bottom), (255, 102, 0), 2)
        cv2.putText(frame, name, (left + 2, bottom + 20), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 1)
        # frame = ft.draw_text(frame, (left + 2, bottom + 10), name, 20, (0, 255, 255))
        cv2.imshow('Video', frame)
    # Inspect key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
