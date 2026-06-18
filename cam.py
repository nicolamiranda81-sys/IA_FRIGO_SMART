import cv2
import time
from rilevatore_Oggetti import trova_ritagli

# Variabili globali per la Modalità Live
modalita_live = False
ultimo_tempo_ia = 0
ultime_etichette = []

def cam(cap, riconoscitore, db):
    global modalita_live, ultimo_tempo_ia, ultime_etichette

    ret, frame = cap.read()
    if not ret:
        print("Errore: Impossibile leggere il video.")
        return False

    # Rimpiccioliamo leggermente il frame per alleggerire il calcolo
    frame = cv2.resize(frame, (800, 600))
    
    # --- GESTIONE MODALITÀ LIVE ---
    if modalita_live:
        # 1. Trova i contorni colorati su OGNI fotogramma (veloce, mantiene il video fluido)
        ritagli = trova_ritagli(frame)
        
        tempo_corrente = time.time()
        # 2. Interroga l'IA (pesante) SOLO 1 volta al secondo per non far scattare il video
        if tempo_corrente - ultimo_tempo_ia > 1.0:
            ultime_etichette.clear()
            for ritaglio_img, box in ritagli:
                alimento = riconoscitore.riconosci(ritaglio_img)
                if alimento and alimento.nome.lower() != 'nothing' and alimento.confidenza > 70:
                    # In live non aggiungiamo al Database per non riempirlo, mostriamo solo il nome a schermo
                    ultime_etichette.append((box, f"{alimento.nome} ({int(alimento.confidenza)}%)"))
            ultimo_tempo_ia = tempo_corrente

        # 3. Disegna i rettangoli blu in tempo reale
        for _, (x, y, w, h) in ritagli:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 100, 0), 2)
            
        # 4. Scrive i nomi ricavati dall'ultima scansione IA (massimo 1 secondo fa)
        for (x, y, w, h), etichetta in ultime_etichette:
            cv2.putText(frame, etichetta, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
        cv2.putText(frame, "LIVE MODE: ATTIVO", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    else:
        cv2.putText(frame, "Premi 'v' Scansione | 'l' Live Mode | 'q' Esci", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Frigo Smart - Webcam", frame)

    tasto = cv2.waitKey(1) & 0xFF
    if tasto == ord('q'):
        return False
    elif tasto == ord('l'):
        modalita_live = not modalita_live
        ultime_etichette.clear()
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