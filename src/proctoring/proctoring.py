import cv2
import speech_recognition as sr
import numpy as np
import time

class ProctoringSystem:
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.recognizer = sr.Recognizer()
    
    def monitor_microphone(self):
        mic = sr.Microphone()
        with mic as source:
            print("Calibrating microphone for ambient noise, please be silent...")
            self.recognizer.adjust_for_ambient_noise(source)
            print("Monitoring microphone...")
            audio = self.recognizer.listen(source, timeout=5)
        
        try:
            transcript = self.recognizer.recognize_google(audio)
            print(f"Transcript: {transcript}")
            if len(transcript.split()) > 10:  # Simple heuristic: too many words
                print("Warning: Multiple voices detected!")
                return True
            else:
                print("Microphone input is clear.")
                return False
        except sr.UnknownValueError:
            print("Could not understand audio.")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
        return False
    
    def monitor_camera(self):
        cap = cv2.VideoCapture(0)  # Open the webcam
        face_detected = False
        start_time = time.time()
        
        print("Monitoring camera...")
        while time.time() - start_time < 10:  # Monitor for 10 seconds
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            if len(faces) == 0:
                print("Warning: No face detected!")
            elif len(faces) > 1:
                print("Warning: Multiple faces detected!")
            else:
                face_detected = True
            
            cv2.imshow('Proctoring Camera', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        return face_detected

    def proctor(self):
        camera_warning = self.monitor_camera()
        mic_warning = self.monitor_microphone()

        if mic_warning or not camera_warning:
            print("Proctoring Warning: Suspicious activity detected!")
        else:
            print("Proctoring passed: No suspicious activity detected.")
