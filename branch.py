from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

# ------------------- MongoDB Setup -------------------
client = AsyncIOMotorClient("mongodb+srv://Ahsan12:Ahsan12@botss.rvm4jx6.mongodb.net/")
db = client["attendance_database"]  # IMPORTANT: Must match main.py database name

# Branches data - UPDATE THESE WITH YOUR ACTUAL DEVICE IPs
branches = [
    {"branch_name": "Karachi_Clifton", "device_serial": 995, "device_ip": "192.168.1.109"},
    {"branch_name": "Karachi_Saddar", "device_serial": 996, "device_ip": "192.168.1.110"},
    {"branch_name": "Lahore_Main", "device_serial": 997, "device_ip": "192.168.2.101"},
    {"branch_name": "Islamabad_Center", "device_serial": 998, "device_ip": "192.168.3.101"}
]

async def setup_branches():
    coll = db["branches"]
    
    print("\n=== Setting up branches ===")
    
    # Insert or update branches in MongoDB
    for b in branches:
        result = await coll.update_one(
            {"device_ip": b["device_ip"]},  # Match by IP address
            {"$set": b}, 
            upsert=True
        )
        if result.upserted_id:
            print(f"✓ Inserted branch: {b['branch_name']}")
        else:
            print(f"✓ Updated branch: {b['branch_name']}")
        print(f"  - IP: {b['device_ip']}, Serial: {b['device_serial']}")
    
    # Display all branches in database
    print("\n=== All Branches in Database ===")
    all_branches = await coll.find().to_list(length=100)
    
    if not all_branches:
        print("⚠️  WARNING: No branches found in database!")
    else:
        print(f"Found {len(all_branches)} branch(es):")
        for branch in all_branches:
            print(f"  - Branch: {branch['branch_name']}")
            print(f"    IP: {branch['device_ip']}")
            print(f"    Serial: {branch['device_serial']}")
            print()
    
    print("✅ Branches setup completed!")
    print("\nNOTE: Make sure the device_ip values match your actual device IP addresses.")
    print("Check your device logs to confirm the IP address being sent in events.")

if __name__ == "__main__":
    asyncio.run(setup_branches())