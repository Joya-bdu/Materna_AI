from pymongo import MongoClient
from werkzeug.security import generate_password_hash

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["materna_db"]
users = db["users"]

# Update all passwords
for user in users.find():

    current_password = user["password"]

    # যদি password আগে থেকেই hash না হয়
    if not current_password.startswith("scrypt:") and not current_password.startswith("pbkdf2:"):

        hashed_password = generate_password_hash(current_password)

        users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "password": hashed_password
                }
            }
        )

        print(f'{user["username"]} updated.')

print("All passwords updated successfully.")