import cv2
import numpy as np

def unisci_rettangoli_vicini(rettangoli, soglia=10):
    """ Funzione di appoggio per unire rettangoli vicini a causa dell'imprecisione dell'immagine
    rettangoli: lista di tuple (x, y, w, h)
    soglia: distanza in pixel sotto la quale unire due rettangoli
    """
    if not rettangoli:
        return []

    # Trasformiamo (x, y, w, h) in (x_min, y_min, x_max, y_max) per comodità
    box_formattate = []
    for (x, y, w, h) in rettangoli:
        box_formattate.append([x, y, x + w, y + h])

    unite = []
    
    for box in box_formattate:
        aggiunto = False
        for u_box in unite:
            # Controlliamo se la box attuale è vicina alla u_box (Super Rettangolo)
            # Dilatiamo virtualmente il rettangolo della soglia scelta
            if (box[0] < u_box[2] + soglia and box[2] > u_box[0] - soglia and
                box[1] < u_box[3] + soglia and box[3] > u_box[1] - soglia):
                
                # FONDILI: prendi il minimo per x/y e il massimo per width/height
                u_box[0] = min(u_box[0], box[0])
                u_box[1] = min(u_box[1], box[1])
                u_box[2] = max(u_box[2], box[2])
                u_box[3] = max(u_box[3], box[3])
                
                aggiunto = True
                break
        
        if not aggiunto:
            unite.append(box)

    # Ritrasformiamo i super rettangoli nel formato standard di OpenCV (x, y, w, h)
    risultato = []
    for u_box in unite:
        x, y = u_box[0], u_box[1]
        w, h = u_box[2] - u_box[0], u_box[3] - u_box[1]
        risultato.append((x, y, w, h))

    return risultato

def rimuovi_rettangoli_interni(rettangoli):
    da_mantenere = []
    
    for i, (x1, y1, w1, h1) in enumerate(rettangoli):
        è_interno = False
        
        for j, (x2, y2, w2, h2) in enumerate(rettangoli):
            if i == j: 
                continue 
                
            if (x1 >= x2) and (y1 >= y2) and (x1 + w1 <= x2 + w2) and (y1 + h1 <= y2 + h2):
                è_interno = True
                break 
        if not è_interno:
            da_mantenere.append((x1, y1, w1, h1))
            
    return da_mantenere


def rileva_oggetti(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    #PARAMETRI RICAVATI DAI TESTI PER OTTENERE UN BIANCO REAL
    bianco_min = np.array([0, 0, 80])
    bianco_max = np.array([180, 100, 255])

    #MI FACCIO LA MASCHERA E OTTENGO I CONTORNI DEGLI OGGETTI INDIVIDUATI
    maschera_sfondo = cv2.inRange(hsv, bianco_min, bianco_max)
    maschera_oggetti = cv2.bitwise_not(maschera_sfondo)

    contorni, _ = cv2.findContours(maschera_oggetti, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    lista_rettangoli = []
    #MI FACCIO UNA CORREZZIONE A CAUSA DI SPEZZETAMENTI INEVITABILE DATA LA TECNOLOGIA A DISPOSIZIONE
    for contorno in contorni:
        if cv2.contourArea(contorno) < 500:
            continue
        x, y, w, h = cv2.boundingRect(contorno)
        lista_rettangoli.append((x, y, w, h))
    rif = unisci_rettangoli_vicini(lista_rettangoli)
    rif = rimuovi_rettangoli_interni(rif)
    #CALCOLO FINALE
    oggetti_rilevati = []
    for (x,y,w,h) in rif:
        punto_1 =(x,y)
        punto_2 =(x+w,y+h)
        ritaglio = img[y : y+h, x : x+w]
        oggetti_rilevati.append(ritaglio)
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    return oggetti_rilevati
