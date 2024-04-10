import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    'databaseURL': "https://fceattendancerealtime-default-rtdb.firebaseio.com/"
})

ref = db.reference('Students')

data = {
    '123456': {
        'name': 'Dhanush',
        'major': 'computer science',
        'startYear': 2021,
        'total_attendance': 8,
        'standing':'Good',
        'year': 5,
        'last_attendance': '2021-12-11 00:54:34',
    },
    '852741': {
        'name': 'Emly Blunt',
        'major': 'Economics',
        'startYear': 2021,
        'total_attendance': 12,
        'standing':'Good',
        'year': 2,
        'last_attendance': '2021-12-11 00:54:34',
    },
    '963852': {
        'name': 'Elon Musk',
        'major': 'computer science',
        'startYear': 2020,
        'total_attendance': 6,
        'standing':'Good',
        'year': 3,
        'last_attendance': '2021-12-11 00:54:34',
    },
    
}


for key,value in data.items():
    # print("Keys are :" , key)
    # print("value are :" , value)
    ref.child(key).set(value)