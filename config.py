# ===============================================
# Attendance System Configuration
# ===============================================

# MongoDB Connection
MONGODB_URI = "mongodb+srv://Ahsan12:Ahsan12@botss.rvm4jx6.mongodb.net/"
DB_NAME = "attendance_database"

# Timezone
TIMEZONE = "Asia/Karachi"

# Duplicate Check-in Window (minutes)
DUPLICATE_WINDOW_MIN = 3

# ===============================================
# EMAIL CONFIGURATION
# ===============================================
# For Gmail: Use App Password (not your regular password)
# Steps to get Gmail App Password:
# 1. Go to Google Account Settings
# 2. Security > 2-Step Verification (enable if not already)
# 3. App Passwords > Generate
# 4. Copy the 16-character password

EMAIL_CONFIG = {
    "enabled": False,  # Set to True to enable email notifications
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-app-password",  # Gmail App Password (16 chars)
    
    # Email recipients for daily reports
    "manager_emails": [
        "manager1@company.com",
        "manager2@company.com"
    ]
}

# ===============================================
# SLACK CONFIGURATION
# ===============================================
# Steps to get Slack Webhook URL:
# 1. Go to https://api.slack.com/apps
# 2. Create New App > From Scratch
# 3. Choose workspace
# 4. Incoming Webhooks > Activate
# 5. Add New Webhook to Workspace
# 6. Select channel and copy Webhook URL

SLACK_CONFIG = {
    "enabled": False,  # Set to True to enable Slack notifications
    "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    "channel": "#attendance",
    
    # Notification settings
    "notify_on_checkin": True,
    "notify_on_checkout": True,
    "notify_daily_summary": True,
    "daily_summary_time": "18:00"  # 6 PM
}

# ===============================================
# EXTERNAL API INTEGRATION
# ===============================================
# Configure if you want to sync attendance data to:
# - Payroll system
# - HR management system
# - Custom API endpoint

EXTERNAL_API_CONFIG = {
    "enabled": False,  # Set to True to enable external API sync
    "endpoint": "https://your-api.com/attendance",
    "api_key": "your-api-key",
    "timeout": 10,  # seconds
    
    # Sync settings
    "sync_on_checkin": True,
    "sync_on_checkout": True,
    "retry_on_failure": True,
    "max_retries": 3
}

# ===============================================
# EMPLOYEE CONFIGURATION (Optional)
# ===============================================
# Map employee names to emails for notifications
# This is optional - if not provided, no individual emails sent

EMPLOYEE_EMAILS = {
    "agj": "agj@company.com",
    "john_doe": "john@company.com",
    # Add more employees as needed
}

# ===============================================
# REPORT CONFIGURATION
# ===============================================

REPORT_CONFIG = {
    # Automatic report generation
    "auto_generate_daily": True,
    "auto_generate_weekly": True,
    "auto_generate_monthly": True,
    
    # Report format (excel or csv)
    "default_format": "excel",
    
    # Report storage path
    "output_directory": "./reports",
    
    # Auto-email reports to managers
    "auto_email_reports": False
}

# ===============================================
# WORKING HOURS CONFIGURATION
# ===============================================
# Define office hours for late arrival detection

WORKING_HOURS = {
    "standard_start": "09:00",  # Standard office start time
    "standard_end": "17:00",    # Standard office end time
    "grace_period_minutes": 15,  # Grace period for late arrivals
    
    # Branch-specific hours (optional)
    "branch_hours": {
        "Karachi_Clifton": {"start": "09:00", "end": "18:00"},
        "Karachi_Saddar": {"start": "09:00", "end": "18:00"},
        "Lahore_Main": {"start": "09:30", "end": "17:30"},
        "Islamabad_Center": {"start": "09:00", "end": "17:00"}
    }
}

# ===============================================
# NOTIFICATION TEMPLATES
# ===============================================

NOTIFICATION_MESSAGES = {
    "checkin_slack": "✅ {employee} checked in at {time} [{branch}]",
    "checkout_slack": "🏁 {employee} checked out at {time} - {hours} hours [{branch}]",
    "late_arrival_slack": "⏰ {employee} arrived late at {time} [{branch}]"
}