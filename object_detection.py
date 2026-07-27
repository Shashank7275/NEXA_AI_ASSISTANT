import cv2
from ultralytics import YOLO
import threading
from typing import List, Dict, Any
import time
from livekit.agents import function_tool

# Global model for efficiency (thread-safe for inference)
_model = None

def _load_model():
    global _model
    if _model is None:
        _model = YOLO("yolov11n.pt")  # Auto-downloads latest YOLOv11 nano model [web:1][page:1]

@function_tool
async def detect_objects(conf: float = 0.5) -> Dict[str, Any]:
    _load_model()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return {"error": "Could not open webcam"}
    results = []
    print("Starting real-time object detection. Press 'q' to quit window.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        yolo_results = _model(frame, conf=conf, verbose=False)
        frame_with_boxes = yolo_results[0].plot()
        cv2.imshow('Jarvis Real-Time Object Detection (q to quit)', frame_with_boxes)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    detections = []
    if yolo_results[0].boxes is not None:
        for box in yolo_results[0].boxes:
            cls = int(box.cls[0])
            conf_val = float(box.conf[0])
            name = _model.names[cls]
            detections.append({"class": name, "confidence": conf_val})
    return {
        "status": "success",
        "message": "Real-time object detection completed.",
        "detections": detections[-5:],
        "total_frames": len(results) if results else "Live stream ended"
    }

# Example usage in Jarvis system:
# @function_tool
# async def detect_objects():
#     ...

if __name__ == "__main__":
    pass
