# backend/utils.py
import os
import smtplib
from email.message import EmailMessage


EMAIL_ADDRESS = os.getenv("EMAIL_USER")
EMAIL_PASSWORD =os.getenv("EMAIL_PASS")


def ensure_folder(path: str):
    """Create folder if it does not exist"""
    if not os.path.exists(path):
        os.makedirs(path)


def send_alert_email(
    receiver_email: str,
    severity: str,
    vehicle_count: int,
    impact_score: float,
    clip_path: str
):
    """
    Sends smart accident alert with severity & vehicle count
    """

    msg = EmailMessage()
    msg["Subject"] = f"🚨 Accident Alert | Severity: {severity}"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = receiver_email

    msg.set_content(f"""
🚑 SMART ACCIDENT ALERT

Severity Level  : {severity}
Vehicles Involved: {vehicle_count}
Impact Score   : {impact_score:.2f}

Please find attached 10-second accident footage.

— Smart Accident Detection System
""")

    if clip_path and os.path.exists(clip_path):
        with open(clip_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="video",
                subtype="mp4",
                filename=os.path.basename(clip_path)
            )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print(f"✅ Alert email sent to {receiver_email}")
    except Exception as e:
        print("❌ Email sending failed:", e)
