import cv2
import json
import time

# ── Config ──────────────────────────────────────────────────────────────────
camera_name = input("Enter camera/location name (default: 'cam1'): ").strip() or "cam1"
json_file = f"parking-coords/{camera_name}.json"

try:
    with open(json_file, "r") as f:
        parking_slots = json.load(f)
    for slot in parking_slots.values():
        slot.setdefault("type", "normal")
except Exception:
    parking_slots = {}

# ── Slot appearance ──────────────────────────────────────────────────────────
SLOT_COLORS = {
    "normal": (255, 0, 255),
    "ev": (0, 140, 0),
    "handicap": (255, 0, 0),
}

SLOT_LABELS = {
    "normal": "P",
    "ev": "EV",
    "handicap": "HC",
}

# ── Draw state ───────────────────────────────────────────────────────────────
drawing = False
startPoint = None
currentPoint = None
selected_slot = None  # name of the currently selected slot
mouse_pos = (0, 0)  # track cursor for hover highlight


# ── Helpers ──────────────────────────────────────────────────────────────────
def save_positions():
    import os

    os.makedirs("parking-coords", exist_ok=True)
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
        (int(k.replace("slot_", "")) for k in parking_slots if k.startswith("slot_")),
        default=0,
    )
    return max_slot + 1


def slot_at(x, y):
    for name, data in parking_slots.items():
        box = (data["x1"], data["y1"], data["x2"], data["y2"])
        if is_inside_box(x, y, box):
            return name, data
    return None, None


# ── Mouse callback ────────────────────────────────────────────────────────────
def mouseClick(event, x, y, flags, params):
    global drawing, startPoint, currentPoint, selected_slot, mouse_pos

    if event == cv2.EVENT_MOUSEMOVE:
        mouse_pos = (x, y)
        if drawing:
            currentPoint = (x, y)
        return

    # ── Double-left-click → delete slot ──────────────────────────────────────
    if event == cv2.EVENT_LBUTTONDBLCLK:
        drawing = False
        name, _ = slot_at(x, y)
        if name:
            if selected_slot == name:
                selected_slot = None
            del parking_slots[name]
            save_positions()
        return

    # ── Left button down → select slot OR begin drag ──────────────────────────
    if event == cv2.EVENT_LBUTTONDOWN:
        name, _ = slot_at(x, y)
        if name:
            # Clicked inside an existing slot → select it
            selected_slot = name
        else:
            # Clicked on empty area → deselect and start drawing
            selected_slot = None
            drawing = True
            startPoint = (x, y)
            currentPoint = (x, y)
        return

    # ── Left button up → commit new slot ─────────────────────────────────────
    if event == cv2.EVENT_LBUTTONUP and drawing:
        drawing = False
        currentPoint = (x, y)
        x1, y1, x2, y2 = normalize_box(
            startPoint[0], startPoint[1], currentPoint[0], currentPoint[1]
        )
        if abs(x2 - x1) >= 8 and abs(y2 - y1) >= 8:
            slot_num = get_next_slot_number()
            parking_slots[f"slot_{slot_num}"] = {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "type": "normal",
            }
            save_positions()
        return

    # ── Right-click → deselect ────────────────────────────────────────────────
    if event == cv2.EVENT_RBUTTONDOWN:
        selected_slot = None
        return


# ── Window & callback setup ──────────────────────────────────────────────────
cv2.namedWindow("ParkingMarker")
cv2.setMouseCallback("ParkingMarker", mouseClick)

print(f"\nCamera : {camera_name}")
print(f"File   : {json_file}")
print("─" * 42)
print("  Drag (L-btn)          → add Normal slot")
print("  L-click on slot       → select slot")
print("  E  (slot selected)    → mark as EV")
print("  H  (slot selected)    → mark as Handicap")
print("  N  (slot selected)    → reset to Normal")
print("  Double L-click on box → delete slot")
print("  R-click / Esc         → deselect")
print("  Q                     → quit & save")
print("─" * 42)


# ── Legend helper ─────────────────────────────────────────────────────────────
def draw_legend(img):
    items = [
        ("P  Normal", SLOT_COLORS["normal"]),
        ("EV Electric", SLOT_COLORS["ev"]),
        ("HC Handicap", SLOT_COLORS["handicap"]),
    ]
    x0, y0, pad, h = 10, 10, 6, 22
    box_w = 160
    overlay = img.copy()
    cv2.rectangle(
        overlay,
        (x0 - pad, y0 - pad),
        (x0 + box_w, y0 + len(items) * h + pad),
        (30, 30, 30),
        -1,
    )
    cv2.addWeighted(overlay, 0.55, img, 0.45, 0, img)
    for i, (label, color) in enumerate(items):
        y = y0 + i * h + 14
        cv2.rectangle(img, (x0, y - 10), (x0 + 12, y + 2), color, -1)
        cv2.putText(
            img,
            label,
            (x0 + 18, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (230, 230, 230),
            1,
            cv2.LINE_AA,
        )


# ── Main loop ─────────────────────────────────────────────────────────────────
while True:
    img = cv2.imread("media/carParkImg.png")

    # ── Draw committed slots ──────────────────────────────────────────────────
    for slot_name, slot_data in parking_slots.items():
        x1, y1, x2, y2 = (
            slot_data["x1"],
            slot_data["y1"],
            slot_data["x2"],
            slot_data["y2"],
        )
        stype = slot_data.get("type", "normal")
        color = SLOT_COLORS[stype]
        label = SLOT_LABELS[stype]
        is_selected = slot_name == selected_slot

        # Thicker border + white glow for selected slot
        if is_selected:
            cv2.rectangle(img, (x1 - 2, y1 - 2), (x2 + 2, y2 + 2), (255, 255, 255), 2)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
        else:
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        cv2.putText(
            img,
            slot_name,
            (x1 + 3, y1 - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            color,
            1,
            cv2.LINE_AA,
        )

        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        cv2.putText(
            img,
            label,
            (cx - tw // 2, cy + th // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA,
        )

    # ── Selected slot hint ────────────────────────────────────────────────────
    if selected_slot and selected_slot in parking_slots:
        hint = f"[{selected_slot}] selected  →  E=EV  H=Handicap  N=Normal  DblClick=Delete"
        cv2.putText(
            img,
            hint,
            (10, img.shape[0] - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.46,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )

    # ── Draw rubber-band box while dragging ───────────────────────────────────
    if drawing and startPoint and currentPoint:
        x1, y1, x2, y2 = normalize_box(
            startPoint[0], startPoint[1], currentPoint[0], currentPoint[1]
        )
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 255), 1)

    # ── Legend ────────────────────────────────────────────────────────────────
    draw_legend(img)

    # ── Slot count HUD ────────────────────────────────────────────────────────
    counts = {"normal": 0, "ev": 0, "handicap": 0}
    for s in parking_slots.values():
        counts[s.get("type", "normal")] += 1
    hud = (
        f"Slots: {len(parking_slots)}  "
        f"P:{counts['normal']}  EV:{counts['ev']}  HC:{counts['handicap']}"
    )
    cv2.putText(
        img,
        hud,
        (10, img.shape[0] - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.50,
        (200, 200, 200),
        1,
        cv2.LINE_AA,
    )

    cv2.imshow("ParkingMarker", img)

    # ── Key handling ──────────────────────────────────────────────────────────
    key = cv2.waitKey(16) & 0xFF

    if key == ord("q"):
        break

    elif key == 27:  # Esc → deselect
        selected_slot = None

    elif selected_slot and selected_slot in parking_slots:
        if key == ord("e"):
            parking_slots[selected_slot]["type"] = "ev"
            save_positions()
        elif key == ord("h"):
            parking_slots[selected_slot]["type"] = "handicap"
            save_positions()
        elif key == ord("n"):
            parking_slots[selected_slot]["type"] = "normal"
            save_positions()

cv2.destroyAllWindows()
print(f"\nSaved {len(parking_slots)} slots to {json_file}")
