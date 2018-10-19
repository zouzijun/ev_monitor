# -*- coding: UTF-8 -*-
import face_recognition
import cv2
import os
import numpy as np
import multiprocessing

# Encoding file folder
encoding_file = "./encoding_files"


def recognize_face_from_frame(frameq, dicq, resultq):
    while True:
        if not frameq.empty():
            frame = frameq.get()
            dic = dicq.get()
            # Get face encodings in one frame
            face_locations_in_frame = face_recognition.face_locations(frame)
            face_encodings_in_frame = face_recognition.face_encodings(frame, face_locations_in_frame)
            # Recognize each face in one frame
            for (top, right, bottom, left), face_encoding in zip(face_locations_in_frame, face_encodings_in_frame):
                name = "Unknown"
                # Compare each encoding in face set
                for k, v in dic.items():
                    # results is an array of True/False
                    match = face_recognition.compare_faces([v], face_encoding, tolerance=0.35)
                    if match[0]:
                        name = k
                        break
                # Push result into queue
                res = (name, top, right, bottom, left)
                resultq.put(res)


if __name__ == '__main__':
    cores = multiprocessing.cpu_count()
    print('Core Count = {0}'.format(cores))
    print('current process {0}'.format(os.getpid()))
    pool = multiprocessing.Pool(processes=cores)
    manager = multiprocessing.Manager()

    if cores >= 2:
        calc_task_count = cores - 1
        # Video Capture
        video_capture = cv2.VideoCapture(0)
        # Encoding dictionary
        encoding_dic = {}
        # Read encodings from file
        for file in os.listdir(encoding_file):
            persion_name = file[:(len(file) - 4)]
            encoding = np.fromfile(encoding_file + "/" + file, dtype=np.float64).tolist()
            encoding_dic[persion_name] = encoding

        # Queue for frame
        frame_q = manager.Queue()
        # Queue for face recognize result
        result_q = manager.Queue()
        # Queue for face set
        dic_q = manager.Queue()
        # Construct threads for recognition
        for i in range(calc_task_count):
            pool.apply_async(func=recognize_face_from_frame, args=(frame_q, dic_q, result_q,))

        (name, top, right, bottom, left) = ('?', 0, 0, 0, 0)
        while True:
            # Get one frame
            ret, frame = video_capture.read()
            if ret and frame_q.qsize() < 4:
                dic_q.put(encoding_dic)
                frame_q.put(frame)
            # Draw name
            if not result_q.empty():
                (name, top, right, bottom, left) = result_q.get()
            # Show frame
            cv2.rectangle(frame, (left, top), (right, bottom), (255, 102, 0), 2)
            cv2.putText(frame, name, (left + 2, bottom + 20), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 1)
            cv2.imshow('Video', frame)
            # Inspect key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                pool.close()
                pool.join()
                break
        print('All processes done')
        video_capture.release()
        cv2.destroyAllWindows()
    else:
        print('Processors do not support parallel processing.')
