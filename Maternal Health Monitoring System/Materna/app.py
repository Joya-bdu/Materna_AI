from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from pymongo import MongoClient
from datetime import datetime
from ultralytics import YOLO
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import joblib
import pandas as pd
import cv2
import threading


fall_running = False

SMS_API_KEY = "7vkxID5GV4KqRmLDgqtQbgK13BYKu7u2y00Iz3q9"
# =================================================
# ESP32 API KEY
# =================================================

API_KEY = "materna_secure_api_2026"



# =================================================
# FLASK APP
# =================================================

app = Flask(__name__)
socketio = SocketIO(

    app,

    cors_allowed_origins="*",

    async_mode="threading"

)

app.config["SECRET_KEY"] = "Materna_2026_Secure_Key_@123"

# =================================================
# MONGODB
# =================================================


client = MongoClient("mongodb://localhost:27017/")

db = client["materna_db"]

users = db["users"]
predictions = db["predictions"]

consultations = db["consultations"]

chat_messages = db.chat_messages
logs = db["logs"]


# =================================================
# DEFAULT ADMIN
# =================================================

if users.count_documents({"role": "admin"}) == 0:

    users.insert_one({
    "username": "admin",
    "password": generate_password_hash("admin123"),
    "role": "admin"
})

# =================================================
# LOAD AI MODEL
# =================================================

risk_model = joblib.load("models/maternal_model.pkl")

fall_model = YOLO("models/best.pt")

# =================================================
# LIVE DATA VARIABLES
# =================================================

latest_data = {

    "heart_rate": 0,

    "spo2": 0,

    "temperature": 0,

    "prediction": "Waiting...",

    "ecg_prediction": "Normal ECG",

    "latitude": 0,

    "longitude": 0,

    "pressure": 0,

    "fall_status": "Normal Movement",

    "gps_status": "Location Not Available"
}

# =================================================
# HOME
# =================================================

@app.route('/')
def home():

    return redirect('/login')

# =================================================
# LOGIN PAGE
# =================================================

@app.route('/login')
def login():

    return render_template('login.html')

# =================================================
# LOGIN CHECK
# =================================================

@app.route('/login_check', methods=['POST'])
def login_check():

    username = request.form['username']

    password = request.form['password']

    user = users.find_one({
        "username": username
    })

    if user and check_password_hash(user["password"], password):
        logs.insert_one({

            "user": username,

            "action": "Login",

            "time": datetime.now()

        })

        session["username"] = username
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect("/admin")

        elif user["role"] == "doctor":
            return redirect("/doctor")

        elif user["role"] == "patient":
            return redirect("/patient")

    return render_template(
    "login.html",
    error="Invalid Username or Password"
)

# =================================================
# LOGOUT
# =================================================

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

# =================================================
# ADMIN DASHBOARD
# =================================================

@app.route('/admin')
def admin():

    if session.get('role') != "admin":
        return redirect('/login')

    all_users = list(users.find())

    total_users = users.count_documents({})
    total_doctors = users.count_documents({"role": "doctor"})
    total_patients = users.count_documents({"role": "patient"})
    total_predictions = predictions.count_documents({})
    total_consultations = consultations.count_documents({})
    
    

    # Last 5 Predictions
    
    prediction_data = list(
    predictions.find().sort("_id", -1).limit(5)
)

    # Last 5 Consultations
    consultation_data = list(
    consultations.find().sort("_id", -1).limit(5)
)

    return render_template(

    "admin.html",

    users=all_users,

    total_users=total_users,
    total_doctors=total_doctors,
    total_patients=total_patients,

    total_predictions=total_predictions,
    total_consultations=total_consultations,

    predictions=prediction_data,
    consultations=consultation_data

)
    
@app.route("/admin/doctors")
def doctor_list():

    if session.get("role") != "admin":
        return redirect("/login")

    doctors = list(users.find({

        "role": "doctor"

    }))

    return render_template(

        "doctor_list.html",

        doctors=doctors

    )
    
@app.route("/admin/patients")
def patient_list():

    if session.get("role") != "admin":
        return redirect("/login")

    patients = list(users.find({

        "role": "patient"

    }))

    return render_template(

        "patient_list.html",

        patients=patients

    )
    
@app.route("/add_doctor")
def add_doctor():

    if session.get("role") != "admin":
        return redirect("/login")

    return render_template("add_doctor.html")

@app.route("/add_patient")
def add_patient():

    if session.get("role") != "admin":
        return redirect("/login")

    doctors = list(users.find({"role": "doctor"}))

    return render_template(
        "add_patient.html",
        doctors=doctors
    )

@app.route("/save_doctor", methods=["POST"])
def save_doctor():

    if session.get("role") != "admin":
        return redirect("/login")

    existing = users.find_one({
        "username": request.form["username"]
    })

    if existing:
        return "Username already exists"

    users.insert_one({

        "full_name": request.form["full_name"],

        "username": request.form["username"],

        "password": generate_password_hash(request.form["password"]),

        "role": "doctor",

        "phone": request.form["phone"],

        "hospital": request.form["hospital"],

        "specialization": request.form["specialization"],

        "qualification": request.form["qualification"],

        "bmdc": request.form["bmdc"],

        "experience": request.form["experience"]

    })

    return redirect("/admin/doctors")

@app.route("/save_patient", methods=["POST"])
def save_patient():

    if session.get("role") != "admin":
        return redirect("/login")
    
    existing = users.find_one({
        "username": request.form["username"]
    })

    if existing:
        return "Username already exists"

    users.insert_one({

        "full_name": request.form["full_name"],
        "username": request.form["username"],
        "password": generate_password_hash(request.form["password"]),
        "role": "patient",

        "age": int(request.form["age"]),
        "gender": request.form["gender"],
        "phone": request.form["phone"],
        "blood_group": request.form["blood_group"],
        "address": request.form["address"],
        "emergency_contact": request.form["emergency_contact"],
        "pregnancy_week": int(request.form["pregnancy_week"]),
        "weight": int(request.form["weight"]),
        "height": int(request.form["height"]),
        "assigned_doctor": request.form["assigned_doctor"]

    })

    return redirect("/admin/patients")

@app.route("/edit_doctor/<username>")
def edit_doctor(username):

    if session.get("role") != "admin":
        return redirect("/login")

    doctor = users.find_one({

        "username": username,

        "role": "doctor"

    })

    return render_template(

        "edit_doctor.html",

        doctor=doctor

    )
    
@app.route("/update_doctor", methods=["POST"])
def update_doctor():

    if session.get("role") != "admin":
        return redirect("/login")

    users.update_one(

        {

            "username": request.form["username"]

        },

        {

            "$set": {

                "full_name": request.form["full_name"],

                "phone": request.form["phone"],

                "hospital": request.form["hospital"],

                "specialization": request.form["specialization"],

                "qualification": request.form["qualification"],

                "bmdc": request.form["bmdc"],

                "experience": request.form["experience"]

            }

        }

    )

    return redirect("/admin/doctors")

@app.route("/delete_doctor/<username>")
def delete_doctor(username):

    if session.get("role") != "admin":
        return redirect("/login")

    users.delete_one({

        "username": username,

        "role": "doctor"

    })

    return redirect("/admin/doctors")

@app.route("/edit_patient/<username>")
def edit_patient(username):

    if session.get("role") != "admin":
        return redirect("/login")

    patient = users.find_one({

        "username": username,

        "role": "patient"

    })

    doctors = list(users.find({

        "role": "doctor"

    }))

    return render_template(

        "edit_patient.html",

        patient=patient,

        doctors=doctors

    )
    
@app.route("/update_patient", methods=["POST"])
def update_patient():

    if session.get("role") != "admin":
        return redirect("/login")

    users.update_one(

        {

            "username": request.form["username"]

        },

        {

            "$set": {

                "full_name": request.form["full_name"],

                "age": int(request.form["age"]),

                "phone": request.form["phone"],

                "blood_group": request.form["blood_group"],

                "pregnancy_week": int(request.form["pregnancy_week"]),

                "assigned_doctor": request.form["assigned_doctor"]

            }

        }

    )

    return redirect("/admin/patients")

@app.route("/delete_patient/<username>")
def delete_patient(username):

    if session.get("role") != "admin":
        return redirect("/login")

    users.delete_one({

        "username": username,

        "role": "patient"

    })

    return redirect("/admin/patients")



@app.route("/admin/consultations")
def consultation_list():

    if session.get("role") != "admin":
        return redirect("/login")

    consultation_data = list(

        consultations.find()

    )

    return render_template(

        "consultation_list.html",

        consultations=consultation_data

    )
    
@app.route("/admin/predictions")
def prediction_history():

    if session.get("role") != "admin":
        return redirect("/login")

    prediction_data = list(

        predictions.find()

    )

    return render_template(

        "prediction_history.html",

        predictions=prediction_data

    )
# =================================================
# ADD USER
# =================================================

@app.route('/add_user', methods=['POST'])
def add_user():

    if session.get('role') != "admin":

        return redirect('/login')

    username = request.form['username']

    password = request.form['password']

    role = request.form['role']

    doctor = request.form.get('doctor')

    # =================================================
    # PATIENT / DOCTOR DETAILS
    # =================================================

    full_name = request.form.get('full_name')

    age = request.form.get('age')

    gender = request.form.get('gender')

    phone = request.form.get('phone')

    blood_group = request.form.get('blood_group')

    address = request.form.get('address')

    emergency_contact = request.form.get('emergency_contact')

    specialization = request.form.get('specialization')

    hospital = request.form.get('hospital')

    experience = request.form.get('experience')

    pregnancy_week = request.form.get("pregnancy_week")

    weight = request.form.get("weight")

    height = request.form.get("height")

    # =================================================
    # CHECK USER EXISTS
    # =================================================

    existing_user = users.find_one({

        "username": username
    })

    if existing_user:

        return "User Already Exists"

    # =================================================
    # SAVE USER
    # =================================================

    users.insert_one({

        "username": username,

        "password": generate_password_hash(password),

        "role": role,

        "assigned_doctor": doctor,

        "full_name": full_name,

        "age": age,

        "gender": gender,

        "phone": phone,

        "blood_group": blood_group,

        "address": address,

        "emergency_contact": emergency_contact,

        "specialization": specialization,

        "hospital": hospital,

        "experience": experience,
        "pregnancy_week": pregnancy_week,

"weight": weight,

"height": height
    })

    return redirect('/admin')
# =================================================
# CONSULT DOCTOR
# =================================================

from datetime import datetime

@app.route("/consult_doctor", methods=["POST"])
def consult_doctor():

    if session.get("role") != "patient":
        return redirect("/login")

    patient = users.find_one({
        "username": session["username"]
    })

    existing = consultations.find_one({

        "patient": patient["username"],
        "status": "Pending"

    })

    if existing:
        return redirect("/consultation")

    consultations.insert_one({

        "patient": patient["username"],
        "doctor": patient["assigned_doctor"],
        "request_time": datetime.now().strftime("%d-%m-%Y %I:%M %p"),
        "status": "Pending",
        "diagnosis": "",
        "medicine": "",
        "advice": ""

    })

    return redirect("/consultation")
@app.route("/send_message", methods=["POST"])
def send_message():

    if session.get("role") != "patient":
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    patient = users.find_one({
        "username": session.get("username")
    })

    if not patient:
        return jsonify({
            "success": False,
            "error": "Patient not found"
        }), 404

    message = request.form.get("message", "").strip()

    if not message:
        return jsonify({
            "success": False,
            "error": "Message cannot be empty"
        }), 400

    doctor_username = patient.get("assigned_doctor")

    if not doctor_username:
        return jsonify({
            "success": False,
            "error": "Doctor is not assigned"
        }), 400

    chat_messages.insert_one({
    "patient": patient["username"],
    "doctor": doctor_username,
    "sender": "patient",
    "message": message,
    "time": datetime.now(),
    "read": False
})

    return jsonify({
        "success": True,
        "message": "Message sent successfully"
    })
    
    # =================================================
# GET CHAT MESSAGES
# =================================================

@app.route("/get_messages/<patient_username>")
def get_messages(patient_username):

    if session.get("role") not in ["patient", "doctor"]:
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    current_username = session.get("username")
    current_role = session.get("role")

    # =============================================
    # PATIENT CHAT
    # =============================================

    if current_role == "patient":

        patient = users.find_one({
            "username": current_username,
            "role": "patient"
        })

        if not patient:
            return jsonify({
                "success": False,
                "error": "Patient not found"
            }), 404

        # Patient শুধু নিজের message দেখতে পারবে
        if patient_username != current_username:
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 403

        doctor_username = patient.get("assigned_doctor")

        query = {
            "patient": current_username,
            "doctor": doctor_username
        }

    # =============================================
    # DOCTOR CHAT
    # =============================================

    else:

        patient = users.find_one({
            "username": patient_username,
            "role": "patient",
            "assigned_doctor": current_username
        })

        if not patient:
            return jsonify({
                "success": False,
                "error": "Patient is not assigned to this doctor"
            }), 403

        query = {
            "patient": patient_username,
            "doctor": current_username
        }

    # =============================================
    # LOAD MESSAGES
    # =============================================

    messages = list(
        chat_messages.find(query).sort("time", 1)
    )

    result = []

    for msg in messages:

        message_time = msg.get("time")

        if isinstance(message_time, datetime):
            formatted_time = message_time.strftime("%I:%M %p")

        elif isinstance(message_time, str):
            formatted_time = message_time

        else:
            formatted_time = ""

        result.append({
            "patient": msg.get("patient"),
            "doctor": msg.get("doctor"),
            "sender": msg.get("sender"),
            "message": msg.get("message"),
            "time": formatted_time,
            "read": msg.get("read", False)
        })

    return jsonify(result)

@app.route("/consultation")
def consultation():

    if session.get("role") != "patient":
        return redirect("/login")

    patient = users.find_one({
        "username": session["username"]
    })

    doctor = users.find_one({
        "username": patient["assigned_doctor"]
    })

    messages = list(
        chat_messages.find({
            "patient": patient["username"]
        }).sort("time", 1)
    )

    return render_template(
        "consultation.html",
        doctor=doctor,
        patient=patient,          # ← এই লাইনটি যোগ করো
        messages=messages
    )
# =================================================
# PATIENT DASHBOARD
# =================================================

@app.route('/patient')
def patient():

    if session.get('role') != "patient":
        return redirect('/login')

    patient_data = users.find_one({
        "username": session.get('username')
    })
    
    assigned_doctor = patient_data.get(
        "assigned_doctor",
        "Not Assigned"
    )

    # =================================================
    # DOCTOR DETAILS
    # =================================================

    doctor_data = users.find_one({
        "username": assigned_doctor
    })

    if doctor_data:

        doctor_specialization = doctor_data.get(
            "specialization",
            "General"
        )

        doctor_hospital = doctor_data.get(
            "hospital",
            "Unknown"
        )

    else:

        doctor_specialization = "General"

        doctor_hospital = "Unknown"

    return render_template(

        "patient.html",

        patient=patient_data,

        patient_name=patient_data.get("full_name", ""),

        patient_age=patient_data.get("age", ""),

        patient_gender=patient_data.get("gender", ""),

        patient_blood=patient_data.get("blood_group", ""),

        patient_phone=patient_data.get("phone", ""),

        emergency_contact=patient_data.get("emergency_contact", ""),

        patient_address=patient_data.get("address", ""),

        pregnancy_week=patient_data.get("pregnancy_week", ""),

        patient_weight=patient_data.get("weight", ""),

        patient_height=patient_data.get("height", ""),

        doctor_name=assigned_doctor,

        doctor_specialization=doctor_specialization,

        doctor_hospital=doctor_hospital,

        blood_sugar="-",

        sbp="-",

        dbp="-",

        pressure=latest_data["pressure"],

        gps_status=latest_data["gps_status"],

        fall_status=latest_data["fall_status"],

        latitude=latest_data["latitude"],

        longitude=latest_data["longitude"],
        
    )

# =================================================
# DOCTOR DASHBOARD
# =================================================

@app.route('/doctor')
def doctor():

    if session.get('role') != "doctor":
        return redirect('/login')

    doctor_name = session.get('username')

    doctor_data = users.find_one({
        "username": doctor_name
    })

    assigned_patients = list(users.find({
        "role": "patient",
        "assigned_doctor": doctor_name
    }))

    all_requests = list(
        consultations.find({
            "doctor": doctor_name,
            "status": "Pending"
        })
    )

    requests = []
    seen = set()

    for req in all_requests:

        if req["patient"] not in seen:

            unread = chat_messages.count_documents({

                "patient": req["patient"],
                "sender": "patient",
                "read": False

            })

            req["unread"] = unread

            requests.append(req)

            seen.add(req["patient"])

    return render_template(

        "doctor.html",

        doctor=doctor_data,

        patients=assigned_patients,

        requests=requests

    )
    
@app.route("/doctor_chat/<patient_username>")
def doctor_chat(patient_username):

    if session.get("role") != "doctor":
        return redirect("/login")

    doctor = users.find_one({
        "username": session["username"]
    })

    patient = users.find_one({
        "username": patient_username
    })
    chat_messages.update_many(

    {

        "patient": patient_username,

        "sender": "patient",

        "read": False

    },

    {

        "$set": {

            "read": True

        }

    }

)

    messages = list(
        chat_messages.find({
            "patient": patient_username
        }).sort("time", 1)
    )

    return render_template(
        "doctor_chat.html",
        doctor=doctor,
        patient=patient,
        messages=messages
    )
    
# =================================================
# DOCTOR SEND MESSAGE
# =================================================

@app.route("/doctor_send_message", methods=["POST"])
def doctor_send_message():

    if session.get("role") != "doctor":
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    data = request.get_json(silent=True) or {}

    patient_username = data.get("patient_username")
    message = data.get("message", "").strip()

    if not patient_username or not message:
        return jsonify({
            "success": False,
            "error": "Invalid message"
        }), 400

    doctor_username = session.get("username")

    # Check whether this patient belongs to this doctor
    patient = users.find_one({
        "username": patient_username,
        "role": "patient",
        "assigned_doctor": doctor_username
    })

    if not patient:
        return jsonify({
            "success": False,
            "error": "Patient not assigned to this doctor"
        }), 403

    # Save doctor message
    chat_messages.insert_one({
        "patient": patient_username,
        "doctor": doctor_username,
        "sender": "doctor",
        "message": message,
        "time": datetime.now(),
        "read": False
    })

    return jsonify({
        "success": True,
        "message": "Message sent successfully"
    })
# =================================================
# SOCKET ROOM
# =================================================

def room_name(patient,doctor):

    return f"{patient}_{doctor}"

# =================================================
# JOIN ROOM
# =================================================

@socketio.on("join")

def join(data):

    room=room_name(

        data["patient"],

        data["doctor"]

    )

    join_room(room)

    emit(

        "status",

        {

            "message":"Joined"

        },

        room=room

    )
    # =================================================
# LEAVE ROOM
# =================================================

@socketio.on("leave")

def leave(data):

    room=room_name(

        data["patient"],

        data["doctor"]

    )

    leave_room(room)

# =================================================
# SEND MESSAGE
# =================================================

@socketio.on("send_message")

def handle_send(data):

    room=room_name(

        data["patient"],

        data["doctor"]

    )

    chat_messages.insert_one({

        "doctor":data["doctor"],

        "patient":data["patient"],

        "sender":data["sender"],

        "message":data["message"],

        "time":datetime.now(),

        "read":False

    })

    emit(

        "receive_message",

        data,

        room=room

    )
    
    # =================================================
# TYPING
# =================================================

@socketio.on("typing")

def typing(data):

    room=room_name(

        data["patient"],

        data["doctor"]

    )

    emit(

        "typing",

        data,

        room=room,

        include_self=False

    )
    
    # =================================================
# STOP TYPING
# =================================================

@socketio.on("stop_typing")

def stop_typing(data):

    room=room_name(

        data["patient"],

        data["doctor"]

    )

    emit(

        "stop_typing",

        room=room,

        include_self=False

    )
    # =================================================
# MESSAGE SEEN
# =================================================

@socketio.on("seen")

def seen(data):

    chat_messages.update_many(

        {

            "patient":data["patient"],

            "sender":data["sender"],

            "read":False

        },

        {

            "$set":{

                "read":True

            }

        }

    )

    room=room_name(

        data["patient"],

        data["doctor"]

    )

    emit(

        "seen",

        room=room

    )

# =================================================
# MANUAL AI PREDICTION
# =================================================

@app.route('/predict', methods=['POST'])
def predict():
    if session.get("role") != "patient":
        return redirect("/login")

    age = float(request.form['age'])
    sbp = float(request.form['sbp'])
    dbp = float(request.form['dbp'])
    bs = float(request.form['bs'])
    temp = float(request.form['temp'])
    hr = float(request.form['hr'])

    if age < 18 or age > 60:
        return "Invalid Age"

    if hr < 0 or hr > 250:
        return "Invalid Heart Rate"

    # Dataset-এর BodyTemp Fahrenheit হিসেবে দেওয়া
    if temp < 90 or temp > 110:
        return "Invalid Temperature"

    if sbp < 50 or sbp > 250:
        return "Invalid Systolic BP"

    if dbp < 30 or dbp > 180:
        return "Invalid Diastolic BP"

    if bs < 0 or bs > 30:
        return "Invalid Blood Sugar"

    sample = pd.DataFrame(
        [[age, sbp, dbp, bs, temp, hr]],
        columns=[
            'Age',
            'SystolicBP',
            'DiastolicBP',
            'BS',
            'BodyTemp',
            'HeartRate'
        ]
    )

    prediction = risk_model.predict(sample)

    if prediction[0] == 0:
        result = "Low Risk"
    elif prediction[0] == 1:
        result = "Mid Risk"
    else:
        result = "High Risk"

    predictions.insert_one({
        "patient": session.get("username"),
        "prediction": result,
        "risk": result,
        "age": age,
        "heart_rate": hr,
        "temperature": temp,
        "blood_sugar": bs,
        "sbp": sbp,
        "dbp": dbp,
        "date": datetime.now().strftime("%d-%m-%Y %I:%M %p"),
        "mode": "manual"
    })

    patient_data = users.find_one({
        "username": session.get("username")
    })

    doctor_name = patient_data.get("assigned_doctor", "Not Assigned")

    doctor = users.find_one({
        "username": doctor_name,
        "role": "doctor"
    })

    if doctor:
        doctor_specialization = doctor.get("specialization", "General")
        doctor_hospital = doctor.get("hospital", "Unknown")
    else:
        doctor_specialization = "General"
        doctor_hospital = "Unknown"

    return render_template(
        "patient.html",

        patient=patient_data,

        patient_name=patient_data.get("full_name", ""),
        patient_age=patient_data.get("age", ""),
        patient_gender=patient_data.get("gender", ""),
        patient_blood=patient_data.get("blood_group", ""),
        patient_phone=patient_data.get("phone", ""),
        emergency_contact=patient_data.get("emergency_contact", ""),
        patient_address=patient_data.get("address", ""),
        pregnancy_week=patient_data.get("pregnancy_week", ""),
        patient_weight=patient_data.get("weight", ""),
        patient_height=patient_data.get("height", ""),

        doctor_name=doctor_name,
        doctor_specialization=doctor_specialization,
        doctor_hospital=doctor_hospital,

        # Manual Result
        manual_prediction=result,
        manual_hr=hr,
        manual_temp=temp,
        manual_bs=bs,
        manual_sbp=sbp,
        manual_dbp=dbp,

        # Live Data
        pressure=latest_data["pressure"],
        gps_status=latest_data["gps_status"],
        fall_status=latest_data["fall_status"],
        latitude=latest_data["latitude"],
        longitude=latest_data["longitude"]
    )
# =================================================
# ESP32 LIVE API
# =================================================
@app.route('/predict_api', methods=['POST'])
def predict_api():

    if request.headers.get("X-API-KEY") != API_KEY:
        return jsonify({"error":"Unauthorized"}),401

    global latest_data
    data = request.get_json()

    if not data:
        return jsonify({"error":"No JSON received"}),400

    required = [

        "age",
        "sbp",
        "dbp",
        "bs",
        "temp",
        "hr",
        "spo2",
        "pressure",
        "latitude",
        "longitude",
        "ecg",
        "accel_x",
        "accel_y",
        "accel_z"

    ]

    for key in required:

        if key not in data:

            return jsonify({

                "error":f"{key} missing"

            }),400

    # =================================================
    # FALL DETECTION
    # =================================================

    if abs(data['accel_x']) > 25000 or \
       abs(data['accel_y']) > 25000 or \
       abs(data['accel_z']) > 25000:

        fall_status = "Fall Detected"

    else:

        fall_status = "Normal Movement"

    # =================================================
    # GPS STATUS
    # =================================================

    if data['latitude'] == 0 and data['longitude'] == 0:

        gps_status = "Location Not Available"

    else:

        gps_status = "GPS Tracking Active"

    # =================================================
    # ECG ANALYSIS
    # =================================================

    if data['ecg'] > 3000 or data['ecg'] < 500:

        ecg_prediction = "Abnormal ECG"

    else:

        ecg_prediction = "Normal ECG"

    # =================================================
    # AI MODEL
    # =================================================

    sample = pd.DataFrame(

        [[

            data['age'],

            data['sbp'],

            data['dbp'],

            data['bs'],

            data['temp'],

            data['hr']

        ]],

        columns=[

            'Age',

            'SystolicBP',

            'DiastolicBP',

            'BS',

            'BodyTemp',

            'HeartRate'
        ]
    )

    prediction = risk_model.predict(sample)

    if prediction[0] == 0:

        risk = "Low Risk"

    elif prediction[0] == 1:

        risk = "Mid Risk"

    else:

        risk = "High Risk"

    # =================================================
    # UPDATE LIVE DATA
    # =================================================

    latest_data = {

        "heart_rate": data['hr'],

        "spo2": data['spo2'],

        "temperature": data['temp'],

        "prediction": risk,

        "ecg_prediction": ecg_prediction,

        "latitude": data['latitude'],

        "longitude": data['longitude'],

        "pressure": data['pressure'],

        "fall_status": fall_status,

        "gps_status": gps_status
    }

    # =================================================
    # SAVE DATABASE
    # =================================================

    return jsonify({

        "prediction": risk,

        "ecg_prediction": ecg_prediction,

        "fall_status": fall_status
    })

@app.route("/start_fall")
def start_fall():

    global fall_running

    if fall_running:
        return redirect("/patient")

    fall_running = True

    thread = threading.Thread(target=run_fall_detection)

    thread.daemon = True

    thread.start()

    return redirect("/patient")

def run_fall_detection():

    global fall_running
    global latest_data

    cap = cv2.VideoCapture(0)

    cv2.namedWindow("Materna Fall Detection", cv2.WINDOW_NORMAL)

    cv2.resizeWindow("Materna Fall Detection",800,600)

    while fall_running:

        ret, frame = cap.read()

        if not ret:
            break

        results = fall_model(frame, conf=0.60)

        latest_data["fall_status"]="Normal Movement"

        for box in results[0].boxes:

            cls=int(box.cls[0])

            label=results[0].names[cls]

            if label.lower()=="fall":

                latest_data["fall_status"]="Fall Detected"

        annotated=results[0].plot()

        cv2.imshow("Materna Fall Detection",annotated)

        if cv2.getWindowProperty("Materna Fall Detection",
                                 cv2.WND_PROP_VISIBLE) < 1:

            break

        if cv2.waitKey(1)&0xFF==ord("q"):

            break

    fall_running=False

    cap.release()

    cv2.destroyAllWindows()
    
@app.route("/stop_fall")
def stop_fall():

    global fall_running

    fall_running=False

    return redirect("/patient")
# =================================================
# LIVE DATA API
# =================================================

@app.route('/live_data')
def live_data():

    if "username" not in session:
        return jsonify({"error":"Unauthorized"}),401

    return jsonify(latest_data)


# =================================================
# TEST ROUTE
# =================================================

@app.route('/test')
def test():

    return jsonify({

        "status": "API Working"
    })
@app.route("/emergency", methods=["POST"])
def emergency():
    if session.get("role") != "patient":
        return redirect("/login")

    print("===== Emergency Started =====")

    patient = users.find_one({
        "username": session.get("username")
    })

    doctor = users.find_one({
        "username": patient.get("assigned_doctor"),
        "role": "doctor"
    })
    if not doctor:
        return "Doctor not found"

    message = f"""
Materna Health Monitoring System

Emergency Alert

Patient: {patient['full_name']}

Phone: {patient['phone']}

Pregnancy Week: {patient['pregnancy_week']}

Please contact immediately.
"""

    # এখান থেকেই নতুন code

    url = "https://api.sms.net.bd/sendsms"

    params = {
        "api_key": SMS_API_KEY,
        "msg": message,
        "to": "88" + doctor["phone"]
    }

    logs.insert_one({
        "user": patient["username"],
        "action": "Emergency SOS",
        "time": datetime.now()
    })

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        print("Status:", response.status_code)
        print("Response:", response.text)

    except Exception as e:
        print("SMS Error:", e)

    return "Done"
# =================================================
# RUN SERVER
# =================================================

if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True
    )