import os
import cv2
import shutil
import sqlite3
import datetime
import smtplib
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from email.message import EmailMessage
from model import Detector, classify_severity

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = Detector()

SAVE_DIR = "saved_events"
DB_PATH = "accident_history.db"
os.makedirs(SAVE_DIR, exist_ok=True)

# ---------------- DATABASE ----------------
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS events(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    email TEXT,
    severity TEXT,
    impact REAL,
    vehicles INTEGER,
    video_path TEXT
)
""")
conn.commit()
conn.close()

# ---------------- EMAIL CONFIG ----------------
SENDER_EMAIL = os.getenv("EMAIL_USER", "mthanusha05@gmail.com")
SENDER_PASSWORD = os.getenv("EMAIL_PASS", "zbinunvqqvluzvzt")

def send_alert_email(receiver_email, severity, vehicles, impact, clip_path):
    msg = EmailMessage()
    msg["Subject"] = "🚨 Accident Detected Alert"
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email

    msg.set_content(f"""
🚨 Accident Detected!

Severity       : {severity}
Vehicles       : {vehicles}
Impact Score   : {impact}
""")

    if clip_path and os.path.exists(clip_path):
        with open(clip_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="video",
                subtype="mp4",
                filename=os.path.basename(clip_path)
            )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

# ---------------- CORE DETECTION ----------------
def detect_accident(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)

    cap.release()

    if len(frames) < 2:
        return None

    # ---------- MOTION ANALYSIS ----------
    motion_scores = []
    for i in range(1, len(frames)):
        prev = cv2.cvtColor(frames[i - 1], cv2.COLOR_BGR2GRAY)
        curr = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(
            prev, curr, None, 0.5, 3, 15, 3, 5, 1.2, 0
        )
        mag = cv2.magnitude(flow[..., 0], flow[..., 1])
        motion_scores.append(float(mag.mean()))

    avg_motion = sum(motion_scores) / len(motion_scores)
    peak_motion = max(motion_scores)

    # ❌ FILTER 1: STRONG MOTION CHECK
    if peak_motion < avg_motion * 6:
        return None

    accident_frame = motion_scores.index(peak_motion)
    start = max(0, accident_frame - int(5 * fps))
    end = min(len(frames), accident_frame + int(5 * fps))

    # ---------- VEHICLE TRACKING ----------
    tracked_vehicles = []
    iou_values = []
    IOU_THRESHOLD = 0.45

    for i in range(start, end):
        detections = detector.detect(frames[i])

        for det in detections:
            matched = False
            for tv in tracked_vehicles:
                iou = detector.iou(det["box"], tv["box"])
                iou_values.append(iou)

                if iou > IOU_THRESHOLD:
                    tv["box"] = det["box"]
                    matched = True
                    break

            if not matched:
                tracked_vehicles.append({"box": det["box"]})

    vehicle_count = len(tracked_vehicles)
    max_iou = max(iou_values) if iou_values else 0.0

    # ❌ FILTER 2: AT LEAST 2 VEHICLES
    if vehicle_count < 2:
        return None

    # ❌ FILTER 3: REAL COLLISION REQUIRED
    if max_iou < 0.25:
        return None

    # ---------- SEVERITY ----------
    severity, impact = classify_severity(peak_motion, max_iou)

    # ---------- SAVE CLIP ----------
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    clip_path = os.path.join(SAVE_DIR, f"accident_{ts}.mp4")

    h, w, _ = frames[0].shape
    out = cv2.VideoWriter(
        clip_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (w, h)
    )

    for i in range(start, end):
        out.write(frames[i])
    out.release()

    return {
        "clip": clip_path,
        "severity": severity,
        "impact": impact,
        "vehicles": vehicle_count
    }


# ---------------- API ----------------
@app.post("/detect_accident")
async def detect_accident_api(
    file: UploadFile = File(...),
    email: str = Form(...)
):
    path = os.path.join(SAVE_DIR, file.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    result = detect_accident(path)
    if not result:
        return {"status": "no_accident"}

    send_alert_email(
        email,
        result["severity"],
        result["vehicles"],
        result["impact"],
        result["clip"]
    )

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO events(timestamp,email,severity,impact,vehicles,video_path) VALUES (?,?,?,?,?,?)",
        (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            email,
            result["severity"],
            result["impact"],
            result["vehicles"],
            result["clip"]
        )
    )
    conn.commit()
    conn.close()

    return {
        "status": "accident",
        "email": email,
        "severity": result["severity"],
        "impact": result["impact"],
        "vehicles": result["vehicles"]
    }

@app.get("/get_history")
async def get_history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT timestamp,email,severity,vehicles FROM events ORDER BY id DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()

    return [
        {
            "timestamp": r[0],
            "email": r[1],
            "severity": r[2],
            "vehicles": r[3]
        } for r in rows
    ]
