import cv2
import numpy as np

def _iou(box_a, box_b):
    xa, ya, wa, ha = box_a
    xb, yb, wb, hb = box_b
    x1 = max(xa, xb)
    y1 = max(ya, yb)
    x2 = min(xa + wa, xb + wb)
    y2 = min(ya + ha, yb + hb)
    inter_w = max(0, x2 - x1)
    inter_h = max(0, y2 - y1)
    inter_area = inter_w * inter_h
    area_a = wa * ha
    area_b = wb * hb
    union = area_a + area_b - inter_area
    if union == 0:
        return 0.0
    return inter_area / union


def trova_ritagli(img):
    """
    Riceve un'immagine OpenCV, individua gli oggetti tramite sogliatura HSV
    (separa gli oggetti colorati dallo sfondo chiaro del frigo) e restituisce
    una lista di tuple (immagine_ritagliata, coordinate_box(x,y,w,h)).
    """
    altezza_img, larghezza_img = img.shape[:2]

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

    contorni, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidati = []
    for c in contorni:
        area = cv2.contourArea(c)
        if area < 900:
            continue
        x, y, w, h = cv2.boundingRect(c)
        if w < 50 or h < 45:
            continue
        if w > larghezza_img * 0.70 or h > altezza_img * 0.60:
            continue
        ratio = w / h
        if ratio > 9 or ratio < 0.12:
            continue
        candidati.append((area, x, y, w, h))

    candidati.sort(key=lambda c: c[0], reverse=True)

    ritagli_trovati = []
    box_accettati = []
    for _, x, y, w, h in candidati:
        box = (x, y, w, h)
        sovrapposto = any(_iou(box, accettato) > 0.25 for accettato in box_accettati)
        if sovrapposto:
            continue
        ritaglio = img[y:y+h, x:x+w]
        ritagli_trovati.append((ritaglio, box))
        box_accettati.append(box)

    return ritagli_trovati


def conta_uova(ritaglio_img):
    """Conta le uova singole dentro un ritaglio classificato come 'Uova', usando watershed."""
    grigio = cv2.cvtColor(ritaglio_img, cv2.COLOR_BGR2GRAY)
    sfocato = cv2.GaussianBlur(grigio, (5, 5), 0)

    _, binaria = cv2.threshold(sfocato, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if np.sum(binaria == 255) > np.sum(binaria == 0):
        binaria = cv2.bitwise_not(binaria)

    kernel = np.ones((3, 3), np.uint8)
    binaria = cv2.morphologyEx(binaria, cv2.MORPH_OPEN, kernel, iterations=2)

    dist = cv2.distanceTransform(binaria, cv2.DIST_L2, 5)
    _, sure_fg = cv2.threshold(dist, 0.5 * dist.max(), 255, 0)
    sure_fg = np.uint8(sure_fg)

    n_labels, markers = cv2.connectedComponents(sure_fg)
    markers = markers + 1
    markers[binaria == 0] = 0

    img_per_watershed = cv2.cvtColor(binaria, cv2.COLOR_GRAY2BGR)
    cv2.watershed(img_per_watershed, markers)

    area_minima = (ritaglio_img.shape[0] * ritaglio_img.shape[1]) * 0.015
    box_uova = []
    for label in range(2, n_labels + 1):
        mask_label = np.uint8(markers == label) * 255
        area = cv2.countNonZero(mask_label)
        if area < area_minima:
            continue
        x, y, w, h = cv2.boundingRect(mask_label)
        box_uova.append((x, y, w, h))

    return box_uova