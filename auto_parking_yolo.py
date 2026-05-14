import cv2
import pickle
import numpy as np
from ultralytics import YOLO

# ── Config ────────────────────────────────────────────────────────────────────
IMAGE_PATH   = 'image2.jpg'   # your parking lot image
OUTPUT_FILE  = 'CarParkPs'       # compatible with your original code
CONF_THRESH  = 0.3                # lower = catch more cars, higher = fewer false positives
IOU_THRESH   = 0.4                # overlap threshold for NMS

# COCO class IDs for vehicles
VEHICLE_CLASSES = {
    2:  'car',
    3:  'motorcycle',
    5:  'bus',
    7:  'truck',
}
# ─────────────────────────────────────────────────────────────────────────────


def detect_parking_spaces(image_path, conf=CONF_THRESH):
    """
    Detect parked vehicles in a top-down parking lot image using YOLOv8.
    Returns list of (x, y, w, h) bounding boxes and saves (x, y) to CarParkPos.
    """
    # Load pretrained YOLOv8 model (downloads automatically on first run ~6MB)
    model = YOLO('yolov8n.pt')

    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot load image: {image_path}")

    print(f"[*] Running YOLO detection on '{image_path}'...")
    results = model(img, conf=conf, iou=IOU_THRESH, verbose=False)[0]

    boxes = []
    for box in results.boxes:
        cls_id = int(box.cls[0])
        if cls_id not in VEHICLE_CLASSES:
            continue
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        w, h = x2 - x1, y2 - y1
        confidence = float(box.conf[0])
        boxes.append((x1, y1, w, h, confidence, VEHICLE_CLASSES[cls_id]))

    print(f"[✓] Detected {len(boxes)} vehicles")
    return img, boxes


def refine_boxes(boxes, img_shape):
    """
    Optional: normalize box sizes to a consistent parking space size.
    Useful when YOLO boxes vary slightly due to partial occlusion.
    """
    if not boxes:
        return boxes

    widths  = [b[2] for b in boxes]
    heights = [b[3] for b in boxes]

    # Use median size as the standard parking space size
    med_w = int(np.median(widths))
    med_h = int(np.median(heights))

    print(f"[*] Median space size: {med_w}w x {med_h}h px")
    print(f"    (Update width={med_w}, height={med_h} in your main script)")

    refined = []
    for (x, y, w, h, conf, label) in boxes:
        # Re-center box using median size
        cx = x + w // 2
        cy = y + h // 2
        nx = cx - med_w // 2
        ny = cy - med_h // 2
        refined.append((nx, ny, med_w, med_h, conf, label))

    return refined, med_w, med_h


def save_positions(boxes, filename=OUTPUT_FILE):
    """Save top-left (x, y) of each box — compatible with original CarParkPos format."""
    posList = [(x, y) for (x, y, w, h, *_) in boxes]
    with open(filename, 'wb') as f:
        pickle.dump(posList, f)
    print(f"[✓] Saved {len(posList)} parking positions to '{filename}'")
    return posList


def visualize(img, boxes, med_w, med_h, save_path='detected_spaces.jpg'):
    out = img.copy()
    for i, (x, y, w, h, conf, label) in enumerate(boxes):
        cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 180), 2)
        cv2.putText(out, f"#{i+1}", (x + 3, y + 15),
                    cv2.FONT_HERSHEY_PLAIN, 0.85, (0, 255, 180), 1)

    # Stats overlay
    overlay = out.copy()
    cv2.rectangle(overlay, (0, 0), (420, 55), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.7, out, 0.3, 0, out)
    cv2.putText(out, f"Detected: {len(boxes)} spaces  |  Size: {med_w}x{med_h}px",
                (10, 35), cv2.FONT_HERSHEY_DUPLEX, 0.85, (255, 255, 255), 1)

    cv2.imwrite(save_path, out)
    print(f"[✓] Visualization saved to '{save_path}'")

    # Show result
    # Resize for display if image is large
    dh, dw = out.shape[:2]
    scale = min(1.0, 1200 / dw, 800 / dh)
    display = cv2.resize(out, (int(dw * scale), int(dh * scale)))
    cv2.imshow("Auto-Detected Parking Spaces (press any key to close)", display)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def main():
    # 1. Detect vehicles
    img, boxes = detect_parking_spaces(IMAGE_PATH)

    if not boxes:
        print("[!] No vehicles detected. Try lowering CONF_THRESH (e.g. 0.15)")
        return

    # 2. Normalize box sizes to consistent parking space dimensions
    boxes, med_w, med_h = refine_boxes(boxes, img.shape)

    # 3. Save to CarParkPos (compatible with your original occupancy checker)
    posList = save_positions(boxes)

    # 4. Visualize
    visualize(img, boxes, med_w, med_h)

    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Done! Update your main script with:
    width  = {med_w}
    height = {med_h}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)


if __name__ == "__main__":
    main()
