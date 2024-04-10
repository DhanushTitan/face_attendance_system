import os
from flask import Flask, render_template, Response, request, redirect, url_for
import cv2
import face_recognition
from firebase_admin import credentials, db, initialize_app, storage
import pickle
from datetime import datetime
import numpy as np
import base64

app = Flask(__name__)

cred = credentials.Certificate("serviceAccountKey.json")
initialize_app(cred, {
    'databaseURL': "https://fceattendancerealtime-default-rtdb.firebaseio.com/",
    'storageBucket': "fceattendancerealtime.appspot.com",
})

camera = cv2.VideoCapture(0)

file = open('EncodeFile.p', 'rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentIds = encodeListKnownWithIds
ref = db.reference('Students')
bucket = storage.bucket()

# Define the folder path for uploading images
folderPath = "Images"

def mark_attendance(student_id):
    # Mark attendance and store attendance history
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    db.reference(f'Students/{student_id}').update({
        'total_attendance': db.reference(f'Students/{student_id}/total_attendance').get() + 1,
        'last_attendance': current_time
    })
    store_attendance_history(student_id, current_time)


def store_attendance_history(student_id, current_time):
    # Store attendance timestamp in a separate branch
    db.reference(f'Students/{student_id}/attendance_history').push().set(
        current_time)


def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break

        imgS = cv2.resize(frame, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        facesCurFrame = face_recognition.face_locations(imgS)
        encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

        if facesCurFrame:
            for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

                matchIndex = np.argmin(faceDis)

                # if matches[matchIndex]:
                #     # Update the student information using studentIds[matchIndex]
                #     student_id = studentIds[matchIndex]
                #     student_info = db.reference(f'Students/{student_id}').get()
                #     if student_info is not None:  # Check if student_info is not None
                #         print(student_info)
                #         if student_info == True:
                #         # Check if attendance is not already marked in the last minute
                            
                #             last_attendance_time = datetime.strptime(
                #                 student_info.get('last_attendance', '1970-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S.%f")
                #             if (datetime.now() - last_attendance_time).total_seconds() / 60 > 60:
                #                 # Perform any other actions or display student_info as needed
                #                 print(f"Marked attendance for {student_info['name']}")
                #                 mark_attendance(student_id)
                if matches[matchIndex]:
                    student_id = studentIds[matchIndex]
                    student_info = db.reference(f'Students/{student_id}').get()
                    if student_info is not None:
                        # print(student_info)
                        last_attendance_time = datetime.strptime(
                            student_info.get('last_attendance', '1970-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S.%f")
                        if (datetime.now() - last_attendance_time).total_seconds() / 60 > 60:
                            print(f"Marked attendance for {student_info['name']}")
                            mark_attendance(student_id)


                            # Redirect to the home page after face recognition
                            # return redirect(url_for('index'))
                    else:
                        print(f"No information found for student ID: {student_id}")

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    students = ref.get()
    return render_template('home.html', students=students)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        major = request.form['major']
        start_year = int(request.form['start_year'])
        total_attendance = int(request.form['total_attendance'])
        student_class = request.form['student_class']  # Corrected the typo
        year = int(request.form['year'])
        last_attendance = request.form['last_attendance']

        new_student = {
            'name': name,
            'major': major,
            'startYear': start_year,
            'total_attendance': total_attendance,
            'student_class': student_class,
            'year': year,
            'last_attendance': last_attendance,
        }

        ref.child(student_id).set(new_student)
        return redirect(url_for('upload'))

    return render_template('add.html')


@app.route('/student')
def detail():
    students = ref.get()
    return render_template('student_view.html', students=students)

@app.route('/video')
def video():
    students = db.reference('Students').get()
    return render_template('video.html', students=students)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/student/<student_id>')
def display_student(student_id):
    student = ref.child(student_id).get()
    image_path = f'Images/{student_id}.png'
    blob = bucket.blob(image_path)
    
    if not blob.exists():
        return "Image not found", 404

    image_data = blob.download_as_bytes()

    base64_image = base64.b64encode(image_data).decode('utf-8')
    return render_template('student_detail.html', student=student, student_id=student_id, image_data=base64_image)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global encodeListKnown, studentIds

    if request.method == 'POST':
        # Handle POST request
        if 'file' not in request.files:
            return "No file part"

        file = request.files['file']

        if file.filename == '':
            return "No selected file"

        if not file.filename.lower().endswith('.png'):
            file.filename = f"{file.filename.split('.')[0]}.png"

        # Upload the file to Firebase Storage
        blob = bucket.blob(f"{folderPath}/{file.filename}")
        blob.upload_from_file(file, content_type='image/png')

        # Extract student ID from filename
        student_id = os.path.splitext(file.filename)[0]
        studentIds.append(student_id)

        # Retrieve the uploaded image from Firebase Storage
        blob = bucket.blob(f"{folderPath}/{file.filename}")
        img_bytes = blob.download_as_string()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Encode the newly uploaded image
        encode = face_recognition.face_encodings(img)[0]
        encodeListKnown.append(encode)

        # Save the updated encodings to a file
        encodeListKnownWithIds = [encodeListKnown, studentIds]
        file = open('EncodeFile.p', 'wb')
        pickle.dump(encodeListKnownWithIds, file)
        file.close()
        return redirect(url_for('index'))
    return render_template('upload_image.html', studentIds=studentIds)

if __name__ == '__main__':
    app.run(debug=True)
