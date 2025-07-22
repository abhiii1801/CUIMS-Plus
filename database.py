from pymongo import MongoClient
from config import get_config
from datetime import datetime
from dotenv import load_dotenv

db = None

def init_db():
    global db
    load_dotenv()
    config = get_config()
    client = MongoClient(config['MONGO_URI'])
    db = client['users']

def get_user(uid):
    users = db['users']
    user = users.find_one({'uid': uid})
    return True if user else False

def insert_new_user(uid):
    collection = db['new_user']
    collection.update_one(
        {"uid": uid},              
        {"$setOnInsert": {"uid": uid}}, 
        upsert=True
    )

def get_user_by_uid(uid: str):
    users = db['users']
    user = users.find_one({'uid': uid})
    return user

def create_user_document(username: str, hashed_password: str):
    users = db['users']
    users.update_one(
        {"uid": username},
        {"$setOnInsert": {
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow(),
            "is_active": True,
            "goal" : 75
        }}, 
        upsert=True
        )

def get_attendance(uid : str):
    attendance_db = db['attendance']
    attendance_data = attendance_db.find_one({'uid': uid})
    return attendance_data['attendance']

def get_timetable(uid : str):
    timetable_db = db['timetable']
    timetable_data = timetable_db.find_one({'uid': uid})
    return timetable_data['timetable']

def get_courses(uid: str):
    courses_db = db['courses']
    courses_data = courses_db.find_one({'uid':uid})
    return courses_data['courses']

def update_attendance(uid: str, attendance_data):
    attendance_db = db['attendance']
    attendance_db.update_one(
        {'uid': uid},
        {'$set': {'attendance': attendance_data}},
        upsert=True
    )

def update_timetable(uid: str, timetable_data):
    timetable_db = db['timetable']
    timetable_db.update_one(
        {'uid': uid},
        {'$set': {'timetable': timetable_data}},
        upsert=True
    )

def update_courses(uid: str, courses_data):
    courses_db = db['courses']
    courses_db.update_one(
        {'uid': uid},
        {'$set': {'courses': courses_data}},
        upsert=True
    )

def save_session(uid, storage_state):
    sessions = db['sessions']
    sessions.update_one(
        {"uid": uid},
        {"$set": {"storage": storage_state}},
        upsert=True
    )

def load_session(uid):
    sessions = db['sessions']
    record = sessions.find_one({"uid": uid})
    return record.get("storage") if record else None

def get_last_updated(uid):
    users = db['sessions']
    last_updated = users.find_one({'uid' : uid})
    return last_updated['last_updated']

def update_last_updated(uid, msg):
    users = db['sessions']
    users.update_one(
        {'uid': uid},
        {"$set": {"last_updated": msg}}
        )

def update_profile(uid: str, profile_data):
    profile_db = db['profile']
    profile_db.update_one(
        {'uid': uid},
        {'$set': {'profile': profile_data}},
        upsert=True
    )

def update_marks(uid: str, marks_data):
    marks_db = db['marks']
    marks_db.update_one(
        {'uid': uid},
        {'$set': {'marks': marks_data}},
        upsert=True
    )

def update_datesheet(uid: str, datesheet_data):
    datesheet_db = db['datesheet']
    datesheet_db.update_one(
        {'uid': uid},
        {'$set': {'datesheet': datesheet_data}},
        upsert=True
    )

def update_result(uid: str, result_data):
    result_db = db['result']
    result_db.update_one(
        {'uid': uid},
        {'$set': {'result': result_data}},
        upsert=True
    )

def update_leaves(uid: str, leaves_data):
    leaves_db = db['leaves']
    leaves_db.update_one(
        {'uid': uid},
        {'$set': {'leaves': leaves_data}},
        upsert=True
    )

def update_fees(uid: str, fees_data):
    fees_db = db['fees']
    fees_db.update_one(
        {'uid': uid},
        {'$set': {'fees': fees_data}},
        upsert=True
    )

def get_marks(uid: str):
    marks_db = db["marks"]
    data = marks_db.find_one({"uid": uid})
    return data["marks"]

def get_result(uid: str):
    result_db = db["result"]
    data = result_db.find_one({"uid": uid})
    return data["result"]

def get_profile(uid: str):
    profile_db = db["profile"]
    data = profile_db.find_one({"uid": uid})
    return data["profile"]

def get_leaves(uid: str):
    leaves_db = db["leaves"]
    data = leaves_db.find_one({"uid": uid})
    return data["leaves"]

def get_fees(uid: str):
    fees_db = db["fees"]
    data = fees_db.find_one({"uid": uid})
    return data["fees"]

def get_datesheet(uid: str):
    datesheet_db = db["datesheet"]
    data = datesheet_db.find_one({"uid": uid})
    return data["datesheet"]

def get_attendance_goal(uid: str):
    users = db['users']
    user = users.find_one({"uid": uid})
    try:
        return user['goal']
    except:
        return 75

def set_goal_value(uid: str, goal: int):
    users = db['users']
    users.update_one({"uid": uid}, {"$set": {"goal": goal}}, upsert=True)
    
def update_session_first(uid, session_id, page):
    session_first_db = db['session_first']
    session_first_db.update_one(
            {'uid': uid},
            {'$set': {'session_id': session_id, 'page': page}},
            upsert=True
        )
    
def get_session_first(uid):
    session_first_db = db['session_first']
    session_first_db.find_one({'uid': uid})
    