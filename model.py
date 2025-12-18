import numpy as np

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except:
    HAS_YOLO = False

class Detector:
    def __init__(self):
        if HAS_YOLO:
            self.model = YOLO("yolov8n.pt")
        else:
            self.model = None

    def detect(self, frame):
        results = []

        if not self.model:
            return results

        output = self.model(frame, verbose=False)[0]
        for box in output.boxes:
            cls = int(box.cls[0])
            label = self.model.names[cls]
            if label not in ["car", "truck", "bus", "motorcycle"]:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            results.append({
                "label": label,
                "box": [x1, y1, x2, y2],
                "center": [cx, cy]
            })

        return results

    def iou(self, A, B):
        xA = max(A[0], B[0])
        yA = max(A[1], B[1])
        xB = min(A[2], B[2])
        yB = min(A[3], B[3])

        inter = max(0, xB - xA) * max(0, yB - yA)
        areaA = (A[2]-A[0]) * (A[3]-A[1])
        areaB = (B[2]-B[0]) * (B[3]-B[1])
        return inter / (areaA + areaB - inter + 1e-6)

def classify_severity(motion_spike, iou_value):
    score = float(motion_spike) * 4 + float(iou_value) * 120

    if score < 30:
        return "Minor", int(score)
    elif score < 60:
        return "Moderate", int(score)
    else:
        return "Severe", int(score)
