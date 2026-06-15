import cv2
from rilevatore_Oggetti import trova_ritagli

def cam(cap, riconoscitore, db):
    ret, frame = cap.read()
    if not ret:
        print("Errore: Impossibile leggere il video.")
        return False

    # Rimpiccioliamo leggermente il frame per alleggerire il calcolo
    frame = cv2.resize(frame, (800, 600))
    cv2.imshow("Webcam - Premi 'v' per scansionare, 'q' per uscire", frame)

    tasto = cv2.waitKey(1) & 0xFF
    if tasto == ord('q'):
        return False
    elif tasto == ord('v'):
        print("\n--- Scansione Avviata ---")
        frame_elaborato = frame.copy()
        
        # 1. Chiamiamo il nostro modulo per avere i ritagli
        ritagli = trova_ritagli(frame)
        print(f"Trovati {len(ritagli)} potenziali oggetti. Inizio Analisi IA...")
        
        # 2. Passiamo ogni ritaglio all'Intelligenza Artificiale
        for indice, (ritaglio_img, (x, y, w, h)) in enumerate(ritagli, 1):
            print(f"Analisi oggetto {indice}/{len(ritagli)} in corso...")
            alimento = riconoscitore.riconosci(ritaglio_img)
            
            # 3. Filtriamo i "Nothing" e salviamo nel Database
            if alimento and alimento.nome.lower() != 'nothing' and alimento.confidenza > 70:
                print(alimento)
                db.aggiungi_alimento(alimento)
                
                etichetta = f"{alimento.nome} ({int(alimento.confidenza)}%)"
                cv2.rectangle(frame_elaborato, (x, y), (x + w, y + h), (0, 255, 0), 3)
                cv2.putText(frame_elaborato, etichetta, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
        cv2.imshow("Risultato Scansione", frame_elaborato)
        
    return True