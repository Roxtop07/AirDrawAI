from flask import Flask, jsonify, request
import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector
from client import publish_canvas, receive_analysis
import threading

app = Flask(__name__)

# Initialize Webcam
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # Width
cap.set(4, 720)   
cap.set(cv2.CAP_PROP_FPS, 50)

# Hand Detector
detector = HandDetector(staticMode=False, maxHands=1, modelComplexity=1, detectionCon=0.7, minTrackCon=0.7)

# Transparent Canvas
canvas = np.zeros((720, 1280, 3), dtype=np.uint8)

# Variables
prev_pos = None
color_index = 0
brush_index = 1
drawing_active = False

# Colors & Brush Sizes
colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 0, 255)]
brush_sizes = [5, 10, 20, 30]
color = colors[color_index]
brush_thickness = brush_sizes[brush_index]
eraser_thickness = 50  

def getHandInfo(img):
    """Detects the hand and returns finger landmarks."""
    hands, img = detector.findHands(img, draw=False, flipType=False)
    if hands:
        hand = hands[0]
        lmList = hand["lmList"]
        fingers = detector.fingersUp(hand)
        return fingers, lmList
    return None, None


def draw(info, canvas, prev_pos, color, thickness):
    """Handles drawing or erasing on the canvas based on finger movement."""
    fingers, lmList = info
    current_pos = None
    mode = "draw"

    if lmList is not None:
        if fingers == [0, 1, 0, 0, 0]:  
            current_pos = lmList[8][:2]
            mode = "draw"
        elif fingers == [0, 1, 1, 0, 0]:  
            current_pos = lmList[12][:2]
            mode = "erase"
        elif fingers == [1, 0, 0, 0, 1]:
            canvas[:] = 0  # Reset Canvas

    if current_pos is not None:
        x, y = map(int, current_pos)
        if mode == "draw":
            if prev_pos is None:
                prev_pos = current_pos
            cv2.line(canvas, tuple(map(int, prev_pos)), tuple(map(int, current_pos)), color, thickness)
        elif mode == "erase":
            cv2.circle(canvas, (x, y), eraser_thickness, (0, 0, 0), -1)  

    return current_pos


def process_drawing():
    """Runs the OpenCV drawing application."""
    global drawing_active, prev_pos
    while drawing_active:
        success, img = cap.read()
        if not success:
            continue

        img = cv2.flip(img, 1)
        info = getHandInfo(img)

        if info:
            fingers, lmList = info
            prev_pos = draw(info, canvas, prev_pos, color, brush_thickness)  

        img_with_canvas = cv2.addWeighted(img, 0.7, canvas, 0.3, 0)
        cv2.imshow("Drawing Canvas", img_with_canvas)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


@app.route('/start', methods=['POST'])
def start_drawing():
    """Starts the drawing process in a new thread."""
    global drawing_active
    if not drawing_active:
        drawing_active = True
        threading.Thread(target=process_drawing, daemon=True).start()
        return jsonify({"message": "Drawing started"}), 200
    return jsonify({"message": "Drawing already running"}), 400


@app.route('/stop', methods=['POST'])
def stop_drawing():
    """Stops the drawing process."""
    global drawing_active
    if drawing_active:
        drawing_active = False
        cap.release()
        cv2.destroyAllWindows()
        return jsonify({"message": "Drawing stopped"}), 200
    return jsonify({"message": "Drawing is not running"}), 400


@app.route('/send_canvas', methods=['POST'])
def send_canvas():
    """Sends the current canvas to AI using MQTT."""
    publish_canvas(canvas)
    return jsonify({"message": "Canvas sent for AI analysis"}), 200


@app.route('/get_analysis', methods=['GET'])
def get_analysis():
    """Retrieves AI analysis results via MQTT."""
    receive_analysis()
    return jsonify({"message": "Listening for AI analysis"}), 200


@app.route('/clear_canvas', methods=['POST'])
def clear_canvas():
    """Clears the drawing canvas."""
    global canvas
    canvas[:] = 0
    return jsonify({"message": "Canvas cleared"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
