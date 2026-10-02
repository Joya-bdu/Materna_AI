from pymongo import MongoClient
from werkzeug.security import generate_password_hash

client = MongoClient("mongodb://localhost:27017/")
db = client["materna_db"]

users = db["users"]
predictions = db["predictions"]
consultations = db["consultations"]
chat_messages = db["chat_messages"]
logs = db["logs"]

# ===========================
# DELETE OLD DATA
# ===========================

users.delete_many({})
predictions.delete_many({})
consultations.delete_many({})
chat_messages.delete_many({})
logs.delete_many({})

print("Old Database Deleted")

# ===========================
# ADMIN
# ===========================

users.insert_one({

    "username":"admin",

    "password":generate_password_hash("admin123"),

    "role":"admin"

})

# ===========================
# DOCTORS
# ===========================

doctors=[

{

"full_name":"Dr. Mahmud Hasan",

"username":"dr_mahmud",

"password":generate_password_hash("1234"),

"role":"doctor",

"phone":"01911111111",

"hospital":"Dhaka Medical College Hospital",

"specialization":"Gynecology",

"qualification":"MBBS, FCPS",

"bmdc":"A12345",

"experience":"10 Years"

},

{

"full_name":"Dr. Tanvir Ahmed",

"username":"dr_tanvir",

"password":generate_password_hash("1234"),

"role":"doctor",

"phone":"01911111112",

"hospital":"Square Hospital",

"specialization":"Obstetrics",

"qualification":"MBBS, FCPS",

"bmdc":"A12346",

"experience":"8 Years"

},

{

"full_name":"Dr. Farhana Islam",

"username":"dr_farhana",

"password":generate_password_hash("1234"),

"role":"doctor",

"phone":"01911111113",

"hospital":"United Hospital",

"specialization":"Gynecology",

"qualification":"MBBS, FCPS",

"bmdc":"A12347",

"experience":"12 Years"

},

{

"full_name":"Dr. Nusrat Jahan",

"username":"dr_nusrat",

"password":generate_password_hash("1234"),

"role":"doctor",

"phone":"01911111114",

"hospital":"Evercare Hospital",

"specialization":"Obstetrics",

"qualification":"MBBS, FCPS",

"bmdc":"A12348",

"experience":"9 Years"

},

{

"full_name":"Dr. Sharmeen Akter",

"username":"dr_sharmeen",

"password":generate_password_hash("1234"),

"role":"doctor",

"phone":"01911111115",

"hospital":"Popular Hospital",

"specialization":"Gynecology",

"qualification":"MBBS, FCPS",

"bmdc":"A12349",

"experience":"15 Years"

}

]

users.insert_many(doctors)

# ===========================
# PATIENTS
# ===========================

patients=[

{
"full_name":"Joya Rani Saha",
"username":"joya01",
"password":generate_password_hash("1234"),
"role":"patient",
"age":22,
"gender":"Female",
"phone":"01992433516",
"blood_group":"B+",
"address":"Narsingdi",
"emergency_contact":"01918179593",
"pregnancy_week":21,
"weight":56,
"height":158,
"assigned_doctor":"dr_mahmud"
},

{
"full_name":"Ritu Saha",
"username":"ritu07",
"password":generate_password_hash("1234"),
"role":"patient",
"age":23,
"gender":"Female",
"phone":"01810000007",
"blood_group":"O-",
"address":"Chattogram",
"emergency_contact":"01890000007",
"pregnancy_week":26,
"weight":58,
"height":157,
"assigned_doctor":"dr_farhana"
},

{
"full_name":"Muna Khatun",
"username":"muna09",
"password":generate_password_hash("1234"),
"role":"patient",
"age":31,
"gender":"Female",
"phone":"01810000009",
"blood_group":"B+",
"address":"Khulna",
"emergency_contact":"01890000009",
"pregnancy_week":38,
"weight":75,
"height":166,
"assigned_doctor":"dr_tanvir"
},

{
"full_name":"Sadia Akter",
"username":"sadia10",
"password":generate_password_hash("1234"),
"role":"patient",
"age":24,
"gender":"Female",
"phone":"01810000010",
"blood_group":"O+",
"address":"Barishal",
"emergency_contact":"01890000010",
"pregnancy_week":22,
"weight":60,
"height":159,
"assigned_doctor":"dr_mahmud"
}

]

users.insert_many(patients)

# ===========================
# SAMPLE PREDICTION
# ===========================

predictions.insert_one({

"patient":"joya01",

"prediction":"Low Risk",

"risk":"Low Risk",

"age":22,

"heart_rate":80,

"temperature":36.7,

"blood_sugar":6.5,

"sbp":120,

"dbp":80,

"date":"30-07-2026",

"mode":"manual"

})

# ===========================
# SAMPLE CONSULTATION
# ===========================

consultations.insert_one({

"patient":"joya01",

"doctor":"dr_mahmud",

"request_time":"30-07-2026",

"status":"Pending",

"diagnosis":"",

"medicine":"",

"advice":""

})

# ===========================
# SAMPLE CHAT
# ===========================

chat_messages.insert_one({

"doctor":"dr_mahmud",

"patient":"joya01",

"sender":"patient",

"message":"Good Morning Doctor",

"time":"30-07-2026",

"read":False

})

# ===========================
# SAMPLE LOG
# ===========================

logs.insert_one({

"user":"admin",

"action":"Database Created",

"time":"30-07-2026"

})

print("===================================")
print("Materna Database Created Successfully")
print("===================================")