import cv2
import threading
from ultralytics import YOLO
import winsound # Built-in Windows sound library (No installation needed)
import time

# --- CONFIGURATION ---

# 1. CAMERA SETUP 
# (Ensure this IP matches your phone's IP right now!)
STREAM_URL = 'http://172.16.125.56:8080/video' 

# 2. MODEL SETUP
model = YOLO('yolov8n.pt') 

# 3. THREAT CONFIGURATION
# 76: Scissors (Simulates Knife)
# 67: Cell Phone (Simulates Detonator/Gun)
# 43: Knife (Real Knife)
# 79: Toothbrush (Simulates Pen/Shiv)
THREAT_CLASSES = [76, 67, 43, 79] 

# Alarm State
alarm_active = False

def play_alarm():
    """Plays a system beep instead of an mp3 file"""
    global alarm_active
    # Beep at 2500Hz for 1000 milliseconds (1 second)
    # This sounds like a high-pitched security alarm
    winsound.Beep(2500, 1000) 
    alarm_active = False

# --- MAIN SURVEILLANCE LOOP ---
print(f"Connecting to Mobile CCTV at: {STREAM_URL} ...")
cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    print("❌ Error: Could not connect to phone camera.")
    print("Check: 1. Phone screen is ON? 2. Same WiFi? 3. Correct IP?")
    exit()

print("✅ SYSTEM ONLINE. SHOW THREATS TO TRIGGER ALARM.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Video stream lost.")
        break

    # Resize frame slightly for faster processing
    frame = cv2.resize(frame, (1020, 600))

    # Run Object Detection
    results = model(frame, stream=True, verbose=False)
    
    threat_detected = False

    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            
            # CHECK IF OBJECT IS A THREAT
            if cls_id in THREAT_CLASSES and conf > 0.4:
                threat_detected = True
                
                # Draw RED Box
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 4)
                
                # Determine Label
                label = "WEAPON DETECTED"
                if cls_id == 79:
                    label = "SHARP OBJECT" # Toothbrush/Pen

                # Add flashing text
                cv2.putText(frame, f"⚠️ {label} ⚠️", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # TRIGGER ALARM LOGIC
    if threat_detected:
        cv2.putText(frame, "!!! SECURITY ALERT !!!", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
        
        if not alarm_active:
            alarm_active = True
            # Run sound in background thread so video doesn't freeze
            threading.Thread(target=play_alarm).start()
            print("!!! ALARM TRIGGERED !!!")

    # Display the System Feed
    cv2.imshow("AI Smart Surveillance System", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()