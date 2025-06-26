from flask import Flask, Response, render_template, jsonify, request
import cv2
import numpy as np
import threading
import time

app = Flask(__name__, static_folder='static', template_folder='templates')

# Initialize face recognizer and detector
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer.yml')
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Webcam initialization with retry
cap = None
for i in range(3):  # Try 3 times to open camera
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        break
    time.sleep(1)

if not cap or not cap.isOpened():
    raise RuntimeError("Could not open camera")

# Settings
color_recognized = (0, 255, 0)
color_unrecognized = (0, 0, 255)
font = cv2.FONT_HERSHEY_SIMPLEX
confidence_threshold = 60

def gen_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, (200, 200))
            label, confidence = recognizer.predict(face)
            
            eyes = eye_cascade.detectMultiScale(face)
            if confidence < confidence_threshold and len(eyes) >= 2:
                color = color_recognized
                text = 'Recognized'
            else:
                color = color_unrecognized
                text = 'Unknown'

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, f"{text} {confidence:.2f}", (x, y-10), 
                       font, 0.9, color, 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    return jsonify({
        'status': 'Active',
        'progress': '75%'
    })

@app.route('/start_auth', methods=['POST'])
def start_auth():
    return jsonify({'status': 'Started'})

@app.route('/stop_auth', methods=['POST'])
def stop_auth():
    return jsonify({'status': 'Stopped'})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows()