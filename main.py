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
                # 3a. Mostra sul frame originale il ripiano/libro trovato (Rettangolo Blu)
                frame_con_ripiano = frame.copy()
                cv2.polylines(frame_con_ripiano, [box], True, (255, 0, 0), 3)
                cv2.imshow("Ripiano Rilevato", frame_con_ripiano)

                # Ordina i punti per avere la giusta corrispondenza (alto-sx, alto-dx...)
                punti_ordinati = ordina_punti_semplice(box)
                
                # 3b. Trasformazione prospettica (il "raddrizzamento")
                LARGHEZZA, ALTEZZA = 400, 550
                punti_destinazione = np.array([[0,0], [LARGHEZZA,0], [LARGHEZZA,ALTEZZA], [0,ALTEZZA]], dtype="float32")
                
                matrice = cv2.getPerspectiveTransform(punti_ordinati, punti_destinazione)
                libro_finale = cv2.warpPerspective(frame, matrice, (LARGHEZZA, ALTEZZA))
                
                # 4. Sottrazione delle immagini per trovare gli oggetti
                ripiano_vuoto = cv2.imread("ripiano_vuoto.jpg")
                if ripiano_vuoto is not None:
                    # Convertiamo in scala di grigi ENTRAMBE le immagini
                    vuoto_grigio = cv2.cvtColor(ripiano_vuoto, cv2.COLOR_BGR2GRAY)
                    finale_grigio = cv2.cvtColor(libro_finale, cv2.COLOR_BGR2GRAY)
                    
                    # 1. Sfocatura LEGGERA: evita di trasformare i bordi delle scritte in macchie giganti
                    vuoto_blur = cv2.GaussianBlur(vuoto_grigio, (5, 5), 0)
                    finale_blur = cv2.GaussianBlur(finale_grigio, (5, 5), 0)

                    # Troviamo la differenza
                    differenza = cv2.absdiff(vuoto_blur, finale_blur)
                    
                    # 2. Threshold: lo alziamo a 45 per tagliare via le ombre più marcate
                    _, diff_binaria = cv2.threshold(differenza, 45, 255, cv2.THRESH_BINARY)
                    
                    # --- 3. PULIZIA AVANZATA CON OPERAZIONI MORFOLOGICHE ---
                    
                    # A) OPENING: cancella le linee sottili prodotte dai disallineamenti della prospettiva
                    kernel_piccolo = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
                    diff_binaria = cv2.morphologyEx(diff_binaria, cv2.MORPH_OPEN, kernel_piccolo)
                    
                    # B) CLOSING E DILATAZIONE per ricompattare e gonfiare gli oggetti veri come le cuffiette
                    kernel_grande = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
                    diff_binaria = cv2.morphologyEx(diff_binaria, cv2.MORPH_CLOSE, kernel_grande)
                    diff_binaria = cv2.dilate(diff_binaria, kernel_grande, iterations=1)
                    
                    # C) Rimuoviamo i falsi positivi sui bordi del libro oscurando i primi 25 pixel esterni
                    cv2.rectangle(diff_binaria, (0, 0), (LARGHEZZA - 1, ALTEZZA - 1), 0, 25)
                    
                    # 5. Trova e disegna i contorni degli oggetti rilevati
                    contorni_oggetti, _ = cv2.findContours(diff_binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    libro_finale_pulito = libro_finale.copy()
                    conta_oggetti = 0
                    for c_ogg in contorni_oggetti:
                        # Filtriamo: Alziamo il minimo a 2500 per ignorare le parole stampate!
                        area = cv2.contourArea(c_ogg)
                        if 2500 < area < 80000:
                            conta_oggetti += 1
                            x, y, w, h = cv2.boundingRect(c_ogg)
                            
                            # --- NOVITÀ: Estrazione e salvataggio dell'oggetto ---
                            # Aggiungiamo 10 pixel di margine per non tagliare l'oggetto a filo
                            margine = 10
                            y1 = max(0, y - margine)
                            y2 = min(ALTEZZA, y + h + margine)
                            x1 = max(0, x - margine)
                            x2 = min(LARGHEZZA, x + w + margine)
                            
                            # Ritagliamo PRIMA di disegnare il rettangolo, così la foto salvata è pulita
                            ritaglio = libro_finale_pulito[y1:y2, x1:x2]
                            cv2.imwrite(f"alimento_rilevato_{conta_oggetti}.jpg", ritaglio)
                            
                            # Disegniamo un rettangolo verde sull'immagine a colori per lo schermo
                            cv2.rectangle(libro_finale, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            cv2.putText(libro_finale, f"Alimento {conta_oggetti}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    cv2.imshow("Oggetti Rilevati sul Ripiano", libro_finale)
                    cv2.imshow("Differenza Assoluta", differenza)
                    cv2.imshow("Oggetti Rilevati (Binario)", diff_binaria)
                else:
                    print("Errore: Immagine 'ripiano_vuoto.jpg' non trovata!")
            else:
                print("Non sono riuscito a trovare un quadrilatero perfetto. Riprova l'inquadratura!")

            


cap.release()
cv2.destroyAllWindows()