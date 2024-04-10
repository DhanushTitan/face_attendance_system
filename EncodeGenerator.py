import cv2 
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    'databaseURL': "https://fceattendancerealtime-default-rtdb.firebaseio.com/",
    'storageBucket': "fceattendancerealtime.appspot.com"
})

# importing Student images 
folderPath = "Images"
PathList = os.listdir(folderPath)
print(PathList)
imgList = []
studentIds = []
for path in PathList:
    imgList.append(cv2.imread(os.path.join(folderPath, path)))
    studentIds.append(os.path.splitext(path)[0])

    fileName = f'{folderPath}/{path}'
    bucket = storage.bucket()
    blob = bucket.blob(fileName)
    blob.upload_from_filename(fileName)


print(blob)
# print(len(imgList))
print(studentIds)
# print("list :" , imgList)



def findEncodings(imgesList):
    encodeList = []
    for img in imgesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

print("Encoding Started ...")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds = [encodeListKnown, studentIds]
print("Encoding Complete")



file = open('EncodeFile.p', 'wb')
pickle.dump(encodeListKnownWithIds, file)
file.close()
print("Encoding File Saved")
