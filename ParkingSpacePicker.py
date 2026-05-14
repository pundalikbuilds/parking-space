import cv2
import pickle

try:
    with open("CarParkPos", "rb") as f:
        posList = pickle.load(f)
except Exception:
    posList = []

drawing = False
startPoint = None
currentPoint = None


def save_positions():
    with open("CarParkPos", "wb") as f:
        pickle.dump(posList, f)


def normalize_box(x1, y1, x2, y2):
    return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)


def is_inside_box(x, y, box):
    x1, y1, x2, y2 = box
    return x1 < x < x2 and y1 < y < y2


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
        posList.append(
            normalize_box(
                startPoint[0], startPoint[1], currentPoint[0], currentPoint[1]
            )
        )
        save_positions()

    elif events == cv2.EVENT_RBUTTONDOWN:
        for i, pos in enumerate(posList):
            if len(pos) == 2:
                x1, y1 = pos
                x2, y2 = x1 + 107, y1 + 48
                box = (x1, y1, x2, y2)
            else:
                box = pos

            if is_inside_box(x, y, box):
                posList.pop(i)
                save_positions()
                break


cv2.namedWindow("Image")
cv2.setMouseCallback("Image", mouseClick)


while True:
    img = cv2.imread("carParkImg.png")
    for pos in posList:
        if len(pos) == 2:
            x1, y1 = pos
            x2, y2 = x1 + 107, y1 + 48
        else:
            x1, y1, x2, y2 = pos

        cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 2)

    if drawing and startPoint and currentPoint:
        x1, y1, x2, y2 = normalize_box(
            startPoint[0], startPoint[1], currentPoint[0], currentPoint[1]
        )
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 255), 2)

    cv2.imshow("Image", img)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
