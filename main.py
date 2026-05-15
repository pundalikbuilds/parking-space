import cv2
import json
import cvzone
import numpy as np
from pathlib import Path
import sys

# Get camera/location name from command-line args or user input
if len(sys.argv) > 2:
    video_path = sys.argv[1]
    camera_name = sys.argv[2]
elif len(sys.argv) > 1:
    video_path = sys.argv[1]
    camera_name = "cam1"
else:
    camera_name = input("Enter camera/location name (default: 'cam1'): ").strip() or "cam1"
    video_path = None

base_dir = Path(__file__).resolve().parent
json_file = base_dir / "parking-coords" / f"{camera_name}.json"

# Video feed
if video_path is None:
    video_path = str(base_dir / "media" / "carPark.mp4")

cap = cv2.VideoCapture(video_path)

try:
    with open(json_file, "r") as f:
        parking_slots = json.load(f)
except Exception:
    print(f"Error: Could not load {json_file}")
    parking_slots = {}


def checkParkingSpace(imgPro):
    spaceCounter = 0
    available_slots = []
    occupied_slots = []

    for slot_name, slot_data in parking_slots.items():
        x1 = slot_data["x1"]
        y1 = slot_data["y1"]
        x2 = slot_data["x2"]
        y2 = slot_data["y2"]

        imgCrop = imgPro[y1:y2, x1:x2]
        # cv2.imshow(str(x * y), imgCrop)
        count = cv2.countNonZero(imgCrop)

        if count < 900:
            color = (0, 255, 0)
            thickness = 5
            spaceCounter += 1
            available_slots.append(slot_name)
        else:
            color = (0, 0, 255)
            thickness = 2
            occupied_slots.append(slot_name)

        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        cvzone.putTextRect(
            img,
            f"{slot_name}: {count}",
            (x1, y2 - 3),
            scale=1,
            thickness=2,
            offset=0,
            colorR=color,
        )

    cvzone.putTextRect(
        img,
        f"Free: {spaceCounter}/{len(parking_slots)}",
        (100, 50),
        scale=3,
        thickness=5,
        offset=20,
        colorR=(0, 200, 0),
    )

    print("\nParking slot status")
    print(
        f"Available ({len(available_slots)}): "
        f"{', '.join(available_slots) if available_slots else 'None'}"
    )
    print(
        f"Occupied ({len(occupied_slots)}): "
        f"{', '.join(occupied_slots) if occupied_slots else 'None'}"
    )


while True:
    if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    success, img = cap.read()
    if not success or img is None:
        print(
            "Error: Could not read a frame from carPark.mp4. Check the file path and video file."
        )
        break
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)
    imgThreshold = cv2.adaptiveThreshold(
        imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16
    )
    imgMedian = cv2.medianBlur(imgThreshold, 5)
    kernel = np.ones((3, 3), np.uint8)
    imgDilate = cv2.dilate(imgMedian, kernel, iterations=1)

    checkParkingSpace(imgDilate)
    cv2.imshow("carParkImg", img)
    # cv2.imshow("ImageBlur", imgBlur)
    # cv2.imshow("ImageThres", imgMedian)
    cv2.waitKey(10)
