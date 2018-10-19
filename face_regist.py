# -*- coding: UTF-8 -*-
import face_recognition
import os
import numpy as np

# Face image set folder
face_set_path = "./image_set"
# Encoding file folder
encoding_file = "./encoding_files"

# Encode each face
for i, img_name in enumerate(os.listdir(face_set_path)):
    image = face_recognition.load_image_file(face_set_path + "/" + img_name)
    name = img_name[:img_name.rfind('.')]
    face_encodings = face_recognition.face_encodings(image)
    if len(face_encodings) > 0:
        one_face_encoding = np.array(face_encodings[0], dtype=np.float64)
        one_face_encoding.tofile(encoding_file + "/" + name + ".dat")
        print("{}-{}: generated.".format(i, name))
    else:
        print("{}-{}: contains no face.".format(i, name))
