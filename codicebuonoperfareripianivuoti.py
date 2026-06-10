import cv2
import numpy as np

print("Accensione webcam in corso...")
cap = cv2.VideoCapture(0) 


def ordina_punti_semplice(box):
    # box è un array di 4 punti (x,y)
    # Calcoliamo la somma e la differenza per trovare gli angoli
    s = box.sum(axis=1)
    diff = np.diff(box, axis=1)
    
    # Ordine: [alto-sx, alto-dx, basso-dx, basso-sx]
    punti = np.zeros((4, 2), dtype="float32")
    punti[0] = box[np.argmin(s)]     # alto-sx (minima somma)
    punti[1] = box[np.argmin(diff)]  # alto-dx (minima differenza)
    punti[2] = box[np.argmax(s)]     # basso-dx (massima somma)
    punti[3] = box[np.argmax(diff)]  # basso-sx (massima differenza)
    return punti
    


while True:
    ret, frame = cap.read()
    
    if not ret:
        print("Errore: Impossibile leggere il video.")
        break

    
    #frame = cv2.flip(frame, 1)
    
    
    cv2.imshow("Webcam Pura", frame)

    tasto = cv2.waitKey(1) & 0xFF
    if tasto == ord('q'):
        break
    elif tasto == ord('v'):
        cv2.imwrite("foto.jpg", frame)
        ##algoritmo di sir Canny per la cattura dei ripiani del frigo
        grigio = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        sfocato = cv2.GaussianBlur(grigio, (5, 5), 0)
        bordi = cv2.Canny(sfocato, 50, 150)
        
        # Uniamo i bordi spezzati: spesso il contorno esterno del libro non è continuo.
        # Dilatando, "saldiamo" i bordi aperti, permettendo al findContours di vedere l'intero libro
        bordi = cv2.dilate(bordi, None, iterations=2)
        bordi = cv2.erode(bordi, None, iterations=1)
        cv2.imshow("TEST: Nuovi Bordi Canny", bordi)
        
        # 2. Estrazione contorno
        contorni, _ = cv2.findContours(bordi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contorni:
            # Ordiniamo i contorni dal più grande al più piccolo e controlliamo i primi 5
            contorni = sorted(contorni, key=cv2.contourArea, reverse=True)[:5]
            
            box = None
            for c in contorni:
                if cv2.contourArea(c) > 15000:
                    perimetro = cv2.arcLength(c, True)
                    
                    # Ricerca dinamica degli angoli con step iper-precisi (0.005)
                    # Questo scavalca il logo Iriun in automatico senza deformare la prospettiva!
                    for tolleranza in np.arange(0.01, 0.15, 0.005):
                        approx = cv2.approxPolyDP(c, tolleranza * perimetro, True)
                        if len(approx) == 4:
                            box = approx.reshape(4, 2)
                            break
                            
                    if box is not None:
                        break
            
            if box is not None:
                # Ordina i punti per avere la giusta corrispondenza (alto-sx, alto-dx...)
                punti_ordinati = ordina_punti_semplice(box)
                
                # 3. Trasformazione prospettica (il "raddrizzamento")
                LARGHEZZA, ALTEZZA = 400, 550
                punti_destinazione = np.array([[0,0], [LARGHEZZA,0], [LARGHEZZA,ALTEZZA], [0,ALTEZZA]], dtype="float32")
                
                matrice = cv2.getPerspectiveTransform(punti_ordinati, punti_destinazione)
                libro_finale = cv2.warpPerspective(frame, matrice, (LARGHEZZA, ALTEZZA))
                
                # Mostra il risultato e salvalo per la sottrazione
                cv2.imshow("RISULTATO FINALE", libro_finale)
                cv2.imwrite("ripiano_vuoto.jpg", libro_finale)
                print("Raddrizzamento completato! Immagine base salvata in 'ripiano_vuoto.jpg'")
            else:
                print("Non sono riuscito a trovare un quadrilatero perfetto. Riprova l'inquadratura!")

            


cap.release()
cv2.destroyAllWindows()