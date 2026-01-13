from motor.motor_asyncio import AsyncIOMotorClient

# ------------------- MongoDB Setup -------------------
client = AsyncIOMotorClient("mongodb+srv://Ahsan12:Ahsan12@botss.rvm4jx6.mongodb.net/")
db = client["attendance_db"]

# Branches data
branches = [
    {"branch_name": "Karachi_Clifton", "device_serial": 995, "device_ip": "192.168.1.109"},
    {"branch_name": "Karachi_Saddar", "device_serial": 996, "device_ip": "192.168.1.110"},
    {"branch_name": "Lahore_Main", "device_serial": 997, "device_ip": "192.168.2.101"},
    {"branch_name": "Islamabad_Center", "device_serial": 998, "device_ip": "192.168.3.101"}
]

coll = db["branches"]

# Insert or update branches in MongoDB
for b in branches:
    coll.update_one({"device_serial": b["device_serial"]}, {"$set": b}, upsert=True)

print("Branches setup completed ✅")
