import cv2
import numpy as np
from tensorflow.keras.models import load_model
from PIL import Image, ImageOps

# =========================
# PARAMETRI MODIFICABILI
# =========================

CONFIDENCE_THRESHOLD = 0.70
MIN_AREA = 900

model = load_model("keras_model.h5", compile=False)
class_names = open("labels.txt", "r").readlines()

image = cv2.imread("foto_frigo4.jpg")

if image is None:
    print("Errore: foto_frigo.jpg non trovata")
    exit()

output = image.copy()
H, W = image.shape[:2]

hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

lower = np.array([0, 25, 35])
upper = np.array([179, 255, 255])

mask = cv2.inRange(hsv, lower, upper)

# =========================
# PULIZIA MASCHERA
# =========================

kernel_open = np.ones((3, 3), np.uint8)
kernel_close = np.ones((12, 12), np.uint8)
kernel_dilate = np.ones((5, 5), np.uint8)

mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close, iterations=1)
mask = cv2.dilate(mask, kernel_dilate, iterations=1)

contours, _ = cv2.findContours(
    mask,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

print("Numero contorni trovati:", len(contours))

boxes = []

for contour in contours:
    area = cv2.contourArea(contour)

    if area < MIN_AREA:
        continue

    x, y, w, h = cv2.boundingRect(contour)

    if w < 50 or h < 45:
        continue

    if w > W * 0.70 or h > H * 0.60:
        continue

    ratio = w / h

    if ratio > 9:
        continue

    if ratio < 0.12:
        continue

    boxes.append((x, y, w, h, area))


def iou(box1, box2):
    x1, y1, w1, h1, _ = box1
    x2, y2, w2, h2, _ = box2

    xa = max(x1, x2)
    ya = max(y1, y2)
    xb = min(x1 + w1, x2 + w2)
    yb = min(y1 + h1, y2 + h2)

    inter_w = max(0, xb - xa)
    inter_h = max(0, yb - ya)

    inter_area = inter_w * inter_h
    area1 = w1 * h1
    area2 = w2 * h2

    union = area1 + area2 - inter_area

    if union == 0:
        return 0

    return inter_area / union


boxes = sorted(boxes, key=lambda b: b[4], reverse=True)

boxes_filtrate = []

for box in boxes:
    sovrapposto = False

    for box_ok in boxes_filtrate:
        if iou(box, box_ok) > 0.25:
            sovrapposto = True
            break

    if not sovrapposto:
        boxes_filtrate.append(box)


for x, y, w, h, area in boxes_filtrate:

    crop = image[y:y+h, x:x+w]

    if crop.size == 0:
        continue

    crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(crop_rgb).convert("RGB")

    pil_image = ImageOps.fit(
        pil_image,
        (224, 224),
        Image.Resampling.LANCZOS
    )

    image_array = np.asarray(pil_image)
    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1

    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized_image_array

    prediction = model.predict(data, verbose=0)

    index = np.argmax(prediction)
    class_name = class_names[index].strip()
    confidence = float(prediction[0][index])

    print(
        "Tentativo:",
        class_name,
        round(confidence, 2),
        "Area:",
        round(float(area), 2),
        "Box:",
        (x, y, w, h)
    )

    if confidence < CONFIDENCE_THRESHOLD:
        print("Scartato per bassa confidenza")
        continue

    label = f"{class_name} {confidence:.2f}"

    print("Rilevato:", label)

    cv2.rectangle(
        output,
        (x, y),
        (x + w, y + h),
        (0, 255, 0),
        2
    )

    cv2.putText(
        output,
        label,
        (x, y - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2
    )

cv2.imwrite("maschera.jpg", mask)
cv2.imwrite("risultato_frigo.jpg", output)

print("Analisi completata.")
print("File creati:")
print("- maschera.jpg")
print("- risultato_frigo.jpg")
