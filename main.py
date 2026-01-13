from fastapi import FastAPI, Request, Form
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import json

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# ------------------- MongoDB Setup -------------------
client = AsyncIOMotorClient("mongodb+srv://Ahsan12:Ahsan12@botss.rvm4jx6.mongodb.net/")
DB_NAME = "attendance_database"
LOCAL_TZ = ZoneInfo("Asia/Karachi")
DUPLICATE_WINDOW_MIN = 3  # Duplicate check-in window

# ------------------- Helper Functions -------------------
def get_local_now():
    return datetime.now(LOCAL_TZ)

def get_collection_name(branch_name):
    now = get_local_now()
    return f"{branch_name}_{now.strftime('%d_%m_%Y')}"

def calculate_total_hours(check_in, check_out):
    if not check_in or not check_out:
        return 0
    dt_in = datetime.strptime(check_in, "%H:%M:%S")
    dt_out = datetime.strptime(check_out, "%H:%M:%S")
    if dt_out < dt_in:
        dt_out += timedelta(days=1)
    return round((dt_out - dt_in).total_seconds() / 3600, 2)

def is_within_duplicate_window(check_in_str, now):
    if not check_in_str:
        return False
    check_in_time = datetime.strptime(check_in_str, "%H:%M:%S")
    check_in_time = datetime.combine(now.date(), check_in_time.time(), tzinfo=LOCAL_TZ)
    diff = (now - check_in_time).total_seconds() / 60
    return diff < DUPLICATE_WINDOW_MIN

# ------------------- Main Event Endpoint -------------------
@app.post("/event")
async def receive_event(event_log: str = Form(...)):
    try:
        # Parse JSON
        data = json.loads(event_log)
        access_event = data.get("AccessControllerEvent", {})

        employee_name = access_event.get("name")
        if not employee_name:  # Only process if name exists
            logging.info(f"Ignored event: No employee name. Device serial: {access_event.get('serialNo')}")
            return {"status": "ignored", "reason": "No employee name"}

        device_serial = access_event.get("serialNo")
        major_event = access_event.get("majorEventType")
        now = get_local_now()
        now_time = now.strftime("%H:%M:%S")

        db = client[DB_NAME]

        # ------------------- Branch Lookup from MongoDB -------------------
        branch_doc = await db["branches"].find_one({"device_serial": device_serial})
        branch_name = branch_doc["branch_name"] if branch_doc else "Unknown_Branch"

        # Only process access events
        if major_event != 5:
            logging.info(f"Ignored non-access event: {employee_name}")
            return {"status": "ignored", "reason": "Not access event"}

        # Mongo collection per branch per day
        coll_name = get_collection_name(branch_name)
        day_coll = db[coll_name]

        # Fetch existing record
        user_doc = await day_coll.find_one({"name": employee_name})

        # ------------------- First Check-In -------------------
        if not user_doc:
            doc = {
                "name": employee_name,
                "check_in": now_time,
                "check_out": None,
                "total_hours": 0,
                "present": True,
                "absent": False,
                "device_serial": device_serial,
                "branch": branch_name
            }
            await day_coll.insert_one(doc)
            logging.info(f"{employee_name} Checked-In at {now_time} [{branch_name}]")
            return {"status": "success", "action": "Check-In", "time": now_time}

        # ------------------- Duplicate Check-In -------------------
        if user_doc.get("check_out") is None and user_doc.get("check_in"):
            if is_within_duplicate_window(user_doc.get("check_in"), now):
                logging.info(f"{employee_name} duplicate Check-In ignored [{branch_name}]")
                return {"status": "ignored", "reason": f"Duplicate Check-In within {DUPLICATE_WINDOW_MIN} mins"}

            # Check-Out
            total_hours = calculate_total_hours(user_doc.get("check_in"), now_time)
            updated_doc = {"check_out": now_time, "total_hours": total_hours}
            await day_coll.update_one({"_id": user_doc["_id"]}, {"$set": updated_doc})
            logging.info(f"{employee_name} Checked-Out at {now_time}, Total Hours: {total_hours} [{branch_name}]")
            return {"status": "success", "action": "Check-Out", "time": now_time}

        # Already Checked-Out
        logging.info(f"{employee_name} already Checked-Out today [{branch_name}]")
        return {"status": "ignored", "reason": "Already checked out"}

    except Exception as e:
        logging.error("Error processing event", exc_info=True)
        return {"error": str(e)}
