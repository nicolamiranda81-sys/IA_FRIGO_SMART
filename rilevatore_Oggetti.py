import cv2
import numpy as np

MIN_AREA = 900

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


def trova_ritagli(img):
    """
    Individua gli alimenti nell'immagine e restituisce:
    [(ritaglio, (x, y, w, h)), ...]
    """

    H, W = img.shape[:2]

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower = np.array([0, 25, 35])
    upper = np.array([179, 255, 255])

    mask = cv2.inRange(hsv, lower, upper)

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

    ritagli_trovati = []

    for x, y, w, h, area in boxes_filtrate:
        ritaglio = img[y:y+h, x:x+w]

        if ritaglio.size == 0:
            continue

        ritagli_trovati.append((ritaglio, (x, y, w, h)))

    return ritagli_trovati