import cv2
import json

# Get camera/location name from user
camera_name = input("Enter camera/location name (default: 'cam1'): ").strip() or "cam1"
json_file = f"{camera_name}.json"

try:
    with open(json_file, "r") as f:
        parking_slots = json.load(f)
except Exception:
    parking_slots = {}

drawing = False
startPoint = None
currentPoint = None


def save_positions():
    with open(json_file, "w") as f:
        json.dump(parking_slots, f, indent=2)


def normalize_box(x1, y1, x2, y2):
    return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)


def is_inside_box(x, y, box):
    x1, y1, x2, y2 = box
    return x1 < x < x2 and y1 < y < y2


def get_next_slot_number():
    if not parking_slots:
        return 1
    max_slot = max(
        (
            int(k.replace("slot_", ""))
            for k in parking_slots.keys()
            if k.startswith("slot_")
        ),
        default=0,
    )
    return max_slot + 1


def mouseClick(events, x, y, flags, params):
    global drawing, startPoint, currentPoint

    if events == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        startPoint = (x, y)
        currentPoint = (x, y)

    elif events == cv2.EVENT_MOUSEMOVE and drawing:
        currentPoint = (x, y)

    elif events == cv2.EVENT_LBUTTONUP and drawing:
        drawing = False
        currentPoint = (x, y)
        x1, y1, x2, y2 = normalize_box(
            startPoint[0], startPoint[1], currentPoint[0], currentPoint[1]
        )
        slot_num = get_next_slot_number()
        parking_slots[f"slot_{slot_num}"] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
        save_positions()

    elif events == cv2.EVENT_RBUTTONDOWN:
        for slot_name, slot_data in list(parking_slots.items()):
            x1 = slot_data["x1"]
            y1 = slot_data["y1"]
            x2 = slot_data["x2"]
            y2 = slot_data["y2"]
            box = (x1, y1, x2, y2)

            if is_inside_box(x, y, box):
                del parking_slots[slot_name]
                save_positions()
                break


cv2.namedWindow("Image")
cv2.setMouseCallback("Image", mouseClick)

print(f"Camera: {camera_name}")
print(f"Saving to: {json_file}")
print("Left-click and drag to mark parking slots")
print("Right-click to remove a slot")
print("Press 'q' to quit")

while True:
    img = cv2.imread("carpv.jpeg")
    for slot_name, slot_data in parking_slots.items():
        x1 = slot_data["x1"]
        y1 = slot_data["y1"]
        x2 = slot_data["x2"]
        y2 = slot_data["y2"]

        cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
        cv2.putText(
            img,
            slot_name,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 0, 255),
            2,
        )

    if drawing and startPoint and currentPoint:
        x1, y1, x2, y2 = normalize_box(
            startPoint[0], startPoint[1], currentPoint[0], currentPoint[1]
        )
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 255), 2)

    cv2.imshow("Image", img)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
