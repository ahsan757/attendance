from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging
from typing import List, Optional, Dict

logging.basicConfig(level=logging.INFO)

# ------------------- Configuration -------------------
client = AsyncIOMotorClient("mongodb+srv://Ahsan12:Ahsan12@botss.rvm4jx6.mongodb.net/")
DB_NAME = "attendance_database"
LOCAL_TZ = ZoneInfo("Asia/Karachi")

class EmployeeManager:
    """Manages employee profiles in the HR system"""
    
    @staticmethod
    async def add_employee(name: str, hourly_rate: float, position: str = "Employee"):
        """Add a new employee to the system"""
        db = client[DB_NAME]
        employee = {
            "name": name,
            "hourly_rate": hourly_rate,
            "position": position,
            "joining_date": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d"),
            "status": "active"
        }
        result = await db["employees"].update_one(
            {"name": name},
            {"$set": employee},
            upsert=True
        )
        return {"status": "success", "name": name, "upserted_id": str(result.upserted_id) if result.upserted_id else None}

    @staticmethod
    async def get_all_employees():
        """Retrieve all employees"""
        db = client[DB_NAME]
        employees = await db["employees"].find().to_list(length=1000)
        for emp in employees:
            emp["_id"] = str(emp["_id"])
        return employees

    @staticmethod
    async def get_employee(name: str):
        """Retrieve a specific employee by name"""
        db = client[DB_NAME]
        employee = await db["employees"].find_one({"name": name})
        if employee:
            employee["_id"] = str(employee["_id"])
        return employee

    @staticmethod
    async def delete_employee(name: str):
        """Delete an employee from the system"""
        db = client[DB_NAME]
        result = await db["employees"].delete_one({"name": name})
        return {"status": "success" if result.deleted_count > 0 else "not_found", "name": name}

class SalaryManager:
    """Calculates salaries based on attendance records"""

    @staticmethod
    async def calculate_salary(employee_name: str, start_date: datetime, end_date: datetime):
        """
        Calculate salary for an employee between two dates
        Dates should be datetime objects
        """
        db = client[DB_NAME]
        employee = await EmployeeManager.get_employee(employee_name)
        if not employee:
            return {"error": f"Employee {employee_name} not found"}

        hourly_rate = employee.get("hourly_rate", 0)
        total_hours = 0
        days_present = 0
        
        # Iterate through dates
        current_date = start_date
        while current_date <= end_date:
            # We need to check all branches for this employee's attendance on this day
            # This is a bit complex because collections are branch_date
            # Let's get all branches first
            branches = await db["branches"].find().to_list(length=100)
            
            for branch in branches:
                branch_name = branch["branch_name"]
                coll_name = f"{branch_name}_{current_date.strftime('%d_%m_%Y')}"
                
                # Check if collection exists and get record
                record = await db[coll_name].find_one({"name": employee_name})
                if record:
                    total_hours += record.get("total_hours", 0)
                    days_present += 1
            
            current_date += timedelta(days=1)

        total_pay = round(total_hours * hourly_rate, 2)
        
        return {
            "employee_name": employee_name,
            "hourly_rate": hourly_rate,
            "total_hours": round(total_hours, 2),
            "days_present": days_present,
            "total_pay": total_pay,
            "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        }

# Helper for date range
from datetime import timedelta