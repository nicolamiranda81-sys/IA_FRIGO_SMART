import cv2
import numpy as np
from tensorflow.keras.models import load_model
from PIL import Image, ImageOps

model = load_model("keras_model.h5", compile=False)
class_names = open("labels.txt", "r").readlines()

image = cv2.imread("foto_frigo.jpg")

if image is None:
    print("Errore: foto_frigo.jpg non trovata")
    exit()

output = image.copy()
H, W = image.shape[:2]

hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

lower = np.array([0, 25, 35])
upper = np.array([179, 255, 255])

mask = cv2.inRange(hsv, lower, upper)

kernel = np.ones((3, 3), np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

contours, _ = cv2.findContours(
    mask,
    cv2.RETR_LIST,
    cv2.CHAIN_APPROX_SIMPLE
)

print("Numero contorni trovati:", len(contours))

boxes_usate = []

for contour in contours:
    area = cv2.contourArea(contour)

    if area < 1500:
        continue

    x, y, w, h = cv2.boundingRect(contour)

    if w < 60 or h < 55:
        continue

    if w > W * 0.50 or h > H * 0.45:
        continue

    ratio = w / h

    if ratio > 5.5:
        continue

    if ratio < 0.18:
        continue

    duplicato = False

    for bx, by, bw, bh in boxes_usate:
        distanza = abs(x - bx) + abs(y - by) + abs(w - bw) + abs(h - bh)

        if distanza < 40:
            duplicato = True
            break

    if duplicato:
        continue

    boxes_usate.append((x, y, w, h))

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
    confidence = prediction[0][index]

    print(
        "Tentativo:",
        class_name,
        round(float(confidence), 2),
        "Area:",
        round(float(area), 2),
        "Box:",
        (x, y, w, h)
    )

    if confidence < 0.50:
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
