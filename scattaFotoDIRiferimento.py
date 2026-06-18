import cv2
import os

def main():
    # Otteniamo la cartella in cui si trova questo script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Definiamo il percorso completo di destinazione per l'immagine
    percorso_salvataggio = os.path.join(base_dir, "base_vuota.jpeg")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Errore: Impossibile accedere alla webcam.")
        return

    print("\n==================================================")
    print("📷 INQUADRA LA SCENA VUOTA (Senza cibi e senza le tue mani)")
    print("👉 Premi la 's' (o la barra spaziatrice) per scattare e salvare la foto.")
    print("👉 Premi 'q' per uscire senza salvare.")
    print("==================================================\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Scatta Foto di Riferimento", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s') or key == 32: # Tasto 's' o Spazio
            cv2.imwrite(percorso_salvataggio, frame)
            print(f"✅ FOTO SALVATA CON SUCCESSO IN:\n{percorso_salvataggio}")
            break
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()