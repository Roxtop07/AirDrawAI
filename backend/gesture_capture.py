import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector
import google.generativeai as genai
from PIL import Image

# Configure Gemini AI
genai.configure(api_key="AIzaSyBHabUZNgZScVBDnr8yNBehuZoMZaqEF0o")
model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize Webcam
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # Width
cap.set(4, 720)   
cap.set(cv2.CAP_PROP_FPS, 50)

# Initialize Hand Detector
detector = HandDetector(staticMode=False, maxHands=1, modelComplexity=1, detectionCon=0.7, minTrackCon=0.7)

# Transparent Canvas
canvas = np.zeros((720, 1280, 3), dtype=np.uint8)

# Variables
prev_pos = None
color_index = 0
brush_index = 1

# Colors & Brush Sizes
colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 0, 255)]
brush_sizes = [5, 10, 20, 30]
color = colors[color_index]
brush_thickness = brush_sizes[brush_index]
eraser_thickness = 50  

# UI Positions
color_wheel_positions = [(50 + i * 80, 50) for i in range(len(colors))]  
brush_positions = [(50, 150 + i * 80) for i in range(len(brush_sizes))]  


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
            canvas[:] = 0

    if current_pos is not None:
        x, y = map(int, current_pos)
        if mode == "draw":
            if prev_pos is None:
                prev_pos = current_pos
            cv2.line(canvas, tuple(map(int, prev_pos)), tuple(map(int, current_pos)), color, thickness)
        elif mode == "erase":
            cv2.circle(canvas, (x, y), eraser_thickness, (0, 0, 0), -1)  

    return current_pos


def detectSelection(lmList):
    """Checks if the user is selecting a color or brush size."""
    global color_index, color, brush_index, brush_thickness

    if lmList is not None:
        x, y = map(int, lmList[8][:2])  

        for i, (cx, cy) in enumerate(color_wheel_positions):
            if cx - 30 < x < cx + 30 and cy - 30 < y < cy + 30:
                color_index = i
                color = colors[color_index]

        for i, (bx, by) in enumerate(brush_positions):
            if bx - 30 < x < bx + 30 and by - 30 < y < by + 30:
                brush_index = i
                brush_thickness = brush_sizes[brush_index]


def SendToAi(canvas):
    """Sends the drawing to Gemini AI for analysis."""
    pil_img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    response = model.generate_content(["solve this math problem          :", pil_img])
    print(response.text)


while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)  
    info = getHandInfo(img)

    if info:
        fingers, lmList = info
        detectSelection(lmList)  
        prev_pos = draw(info, canvas, prev_pos, color, brush_thickness)  

        if fingers == [1, 1, 1, 1, 1]:
            SendToAi(canvas)

    # UI Overlay - Color Wheel
    for i, (cx, cy) in enumerate(color_wheel_positions):
        cv2.circle(img, (cx, cy), 30, colors[i], -1)
        if i == color_index:
            cv2.circle(img, (cx, cy), 35, (255, 255, 255), 2)  

    # UI Overlay - Brush Sizes
    for i, (bx, by) in enumerate(brush_positions):
        cv2.circle(img, (bx, by), 30, (200, 200, 200), -1)
        cv2.circle(img, (bx, by), brush_sizes[i], (0, 0, 0), 2)
        if i == brush_index:
            cv2.circle(img, (bx, by), 35, (255, 255, 255), 2)  

    img_with_canvas = cv2.addWeighted(img, 0.7, canvas, 0.3, 0)
    cv2.imshow("Drawing Canvas", img_with_canvas)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()