import cv2
import numpy as np

def trova_ritagli(img):
    """
    Riceve un'immagine OpenCV, individua gli oggetti, e restituisce una lista
    di tuple contenenti: (immagine_ritagliata, coordinate_box(x,y,w,h))
    """
    altezza_img, larghezza_img = img.shape[:2]
    grigio = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sfocato = cv2.GaussianBlur(grigio, (11, 11), 0)
    
    bordi = cv2.Canny(sfocato, 30, 150)
    bordi = cv2.dilate(bordi, None, iterations=2)
    bordi = cv2.erode(bordi, None, iterations=1)
    
    contorni, _ = cv2.findContours(bordi, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    ritagli_trovati = []
    centri_oggetti_processati = []
    
    for c in contorni:
        area = cv2.contourArea(c)
        if area > 1000:
            x, y, w, h = cv2.boundingRect(c)
            
            if w > (larghezza_img * 0.9) or h > (altezza_img * 0.9):
                continue
            if x <= 5 or y <= 5 or (x + w) >= larghezza_img - 5 or (y + h) >= altezza_img - 5:
                continue
                
            cx, cy = x + w // 2, y + h // 2
            is_duplicate = any(np.sqrt((cx - ox)**2 + (cy - oy)**2) < 50 for ox, oy in centri_oggetti_processati)
            if is_duplicate:
                continue
                
            perimetro = cv2.arcLength(c, True)
            if perimetro > 0:
                approx = cv2.approxPolyDP(c, 0.01 * perimetro, True)
                if len(approx) > 4:
                    ritaglio = img[y:y+h, x:x+w]
                    # Aggiungiamo alla lista il ritaglio e le sue coordinate
                    ritagli_trovati.append((ritaglio, (x, y, w, h)))
                    centri_oggetti_processati.append((cx, cy))
                    
    return ritagli_trovati