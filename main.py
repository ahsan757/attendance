from fastapi import FastAPI, Request, Form
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import json

from integrations import EmployeeManager, SalaryManager
import reports
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

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
        
        # Get IP address from top level (this is the actual device identifier!)
        device_ip = data.get("ipAddress")
        
        access_event = data.get("AccessControllerEvent", {})
        employee_name = access_event.get("name")
        
        logging.info(f"=== EVENT RECEIVED ===")
        logging.info(f"Device IP: {device_ip}")
        logging.info(f"Employee: {employee_name}")
        logging.info(f"Event Type: {access_event.get('majorEventType')}")
        
        if not employee_name:  # Only process if name exists
            logging.info(f"Ignored event: No employee name from device {device_ip}")
            return {"status": "ignored", "reason": "No employee name"}

        if not device_ip:
            logging.warning(f"No device IP found in event!")
            return {"status": "error", "reason": "No device IP found in event"}

        major_event = access_event.get("majorEventType")
        now = get_local_now()
        now_time = now.strftime("%H:%M:%S")

        db = client[DB_NAME]

        # ------------------- Branch Lookup by IP Address -------------------
        branch_doc = await db["branches"].find_one({"device_ip": device_ip})
        
        if branch_doc:
            branch_name = branch_doc["branch_name"]
            device_serial = branch_doc.get("device_serial", "N/A")
            logging.info(f"✓ Branch found: {branch_name} (Serial: {device_serial}) for IP: {device_ip}")
        else:
            branch_name = "Unknown_Branch"
            device_serial = "Unknown"
            logging.warning(f"✗ Branch NOT found for IP: {device_ip}")
            # Log all branches in database for debugging
            all_branches = await db["branches"].find().to_list(length=100)
            logging.info(f"Available branches in DB ({len(all_branches)} total):")
            for b in all_branches:
                logging.info(f"  - {b.get('branch_name')}: IP={b.get('device_ip')}, Serial={b.get('device_serial')}")

        # Only process access events (majorEventType = 5)
        if major_event != 5:
            logging.info(f"Ignored non-access event: {employee_name}, majorEventType: {major_event}")
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
                "device_ip": device_ip,
                "device_serial": device_serial,
                "branch": branch_name
            }
            await day_coll.insert_one(doc)
            logging.info(f"✓ {employee_name} Checked-In at {now_time} [{branch_name}]")
            
            # Integrations removed as per user request
            
            return {
                "status": "success", 
                "action": "Check-In", 
                "time": now_time, 
                "branch": branch_name,
                "employee": employee_name
            }

        # ------------------- Duplicate Check-In -------------------
        if user_doc.get("check_out") is None and user_doc.get("check_in"):
            if is_within_duplicate_window(user_doc.get("check_in"), now):
                logging.info(f"{employee_name} duplicate Check-In ignored [{branch_name}]")
                return {
                    "status": "ignored", 
                    "reason": f"Duplicate Check-In within {DUPLICATE_WINDOW_MIN} mins",
                    "branch": branch_name
                }

            # Check-Out
            total_hours = calculate_total_hours(user_doc.get("check_in"), now_time)
            updated_doc = {"check_out": now_time, "total_hours": total_hours}
            await day_coll.update_one({"_id": user_doc["_id"]}, {"$set": updated_doc})
            logging.info(f"✓ {employee_name} Checked-Out at {now_time}, Total Hours: {total_hours} [{branch_name}]")
            
            # Integrations removed as per user request
            
            return {
                "status": "success", 
                "action": "Check-Out", 
                "time": now_time, 
                "total_hours": total_hours, 
                "branch": branch_name,
                "employee": employee_name
            }

        # Already Checked-Out
        logging.info(f"{employee_name} already Checked-Out today [{branch_name}]")
        return {
            "status": "ignored", 
            "reason": "Already checked out",
            "branch": branch_name
        }

    except Exception as e:
        logging.error("Error processing event", exc_info=True)
        return {"error": str(e)}

# ------------------- HR & Salary Endpoints -------------------

class EmployeeSchema(BaseModel):
    name: str
    hourly_rate: float
    position: Optional[str] = "Employee"

@app.post("/employees")
async def add_employee(employee: EmployeeSchema):
    return await EmployeeManager.add_employee(employee.name, employee.hourly_rate, employee.position)

@app.get("/employees")
async def list_employees():
    return await EmployeeManager.get_all_employees()

@app.get("/employees/{name}")
async def get_employee(name: str):
    emp = await EmployeeManager.get_employee(name)
    if emp:
        return emp
    return {"error": "Employee not found"}

@app.delete("/employees/{name}")
async def delete_employee(name: str):
    return await EmployeeManager.delete_employee(name)

@app.get("/salary/calculate/{employee_name}")
async def calculate_salary(employee_name: str, start_date: str, end_date: str):
    try:
        s_dt = datetime.strptime(start_date, "%d_%m_%Y")
        e_dt = datetime.strptime(end_date, "%d_%m_%Y")
        # Ensure they have timezone info
        s_dt = s_dt.replace(tzinfo=LOCAL_TZ)
        e_dt = e_dt.replace(tzinfo=LOCAL_TZ)
        return await SalaryManager.calculate_salary(employee_name, s_dt, e_dt)
    except Exception as e:
        return {"error": f"Invalid date format. Use DD_MM_YYYY. Error: {str(e)}"}

# ------------------- Branch Endpoints -------------------

class BranchSchema(BaseModel):
    branch_name: str
    device_ip: str
    device_serial: int

@app.post("/branches")
async def add_branch(branch: BranchSchema):
    db = client[DB_NAME]
    result = await db["branches"].update_one(
        {"device_ip": branch.device_ip},
        {"$set": branch.dict()},
        upsert=True
    )
    return {"status": "success", "branch_name": branch.branch_name}

@app.get("/branches")
async def list_branches():
    db = client[DB_NAME]
    branches = await db["branches"].find().to_list(length=100)
    for b in branches:
        b["_id"] = str(b["_id"])
    return branches

@app.delete("/branches/{device_ip}")
async def delete_branch(device_ip: str):
    db = client[DB_NAME]
    result = await db["branches"].delete_one({"device_ip": device_ip})
    return {"status": "success" if result.deleted_count > 0 else "not_found"}

# ------------------- Reporting Endpoints -------------------

@app.get("/reports/daily")
async def get_daily_report(branch_name: Optional[str] = None, format: str = "excel"):
    filename = await reports.generate_daily_report(branch_name=branch_name, format=format)
    if filename:
        return FileResponse(path=filename, filename=filename)
    return {"error": "No records found for today"}

@app.get("/reports/weekly")
async def get_weekly_report(branch_name: Optional[str] = None):
    filename = await reports.generate_weekly_report(branch_name=branch_name)
    if filename:
        return FileResponse(path=filename, filename=filename)
    return {"error": "No records found for the past week"}

@app.get("/reports/monthly")
async def get_monthly_report(year: Optional[int] = None, month: Optional[int] = None, branch_name: Optional[str] = None):
    filename = await reports.generate_monthly_report(year=year, month=month, branch_name=branch_name)
    if filename:
        return FileResponse(path=filename, filename=filename)
    return {"error": "No records found for the specified month"}
