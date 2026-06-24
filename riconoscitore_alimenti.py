import cv2
import numpy as np
import pytesseract
import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
from tensorflow.keras.models import load_model
from Alimento import Alimento
import re

class RiconoscitoreAlimenti:
    def __init__(self):
        self.modello_tm = load_model("keras_model.h5", compile=False) # Assicurati che il modello sia 'keras_model.h5'
        with open("labels.txt", "r") as f:
            self.classi = f.readlines()

    def _estrai_e_normalizza_data(self, testo):
        """Cerca una data nel formato AAAA-MM-GG o GG/MM/AAAA e la normalizza."""
        # Cerca formato YYYY-MM-DD o YYYY/MM/DD
        match = re.search(r'(\d{4})[-/.](\d{2})[-/.](\d{2})', testo)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        
        # Cerca formato DD/MM/YYYY o DD-MM-YYYY
        match = re.search(r'(\d{2})[-/.](\d{2})[-/.](\d{4})', testo)
        if match:
            # Converte in formato standard YYYY-MM-DD per il database
            return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
            
        return None

    def riconosci(self, immagine_cv2):
        # 1. Riconoscimento dell'oggetto (come prima)
        img_resized = cv2.resize(immagine_cv2, (224, 224), interpolation=cv2.INTER_AREA)
        img_array = np.asarray(img_resized, dtype=np.float32).reshape(1, 224, 224, 3)
        img_normalized = (img_array / 127.5) - 1

        predict = self.modello_tm.predict(img_normalized)
        index_win = np.argmax(predict)
        # Pulisce l'etichetta, es. "1 Mela" -> "Mela"
        nome_alimento = self.classi[index_win].strip().split(" ", 1)[1]
        sicurezza = predict[0][index_win] * 100

        # 2. OCR per la data di scadenza (con pre-elaborazione e DEBUG)
        data_scadenza = None
        try:
            gray_image = cv2.cvtColor(immagine_cv2, cv2.COLOR_BGR2GRAY)

            # --- PIPELINE DI PRE-ELABORAZIONE MIGLIORATA ---
            
            # 1. Applichiamo un Median Blur per rimuovere il rumore "sale e pepe" (i puntini)
            #    preservando i bordi del testo.
            blurred_image = cv2.medianBlur(gray_image, 3)

            # 2. Applichiamo la soglia all'immagine con meno rumore per ottenere un B/N pulito.
            _, thresh_image = cv2.threshold(blurred_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # 3. Applichiamo un'operazione di "apertura" per rimuovere il rumore residuo (puntini bianchi)
            #    dopo la sogliatura. Questo è un passo cruciale per pulire l'immagine.
            kernel = np.ones((2,2), np.uint8)
            cleaned_image = cv2.morphologyEx(thresh_image, cv2.MORPH_OPEN, kernel, iterations=1)
            
            # SALVA L'IMMAGINE DI DEBUG per vedere cosa sta vedendo Tesseract
            cv2.imwrite("debug_ocr.jpg", cleaned_image)
            
            # Usiamo una configurazione più specifica per Tesseract, indicando di cercare una singola linea di testo.
            config = "--psm 7"
            testo_estratto = pytesseract.image_to_string(cleaned_image, lang='ita', config=config)
            print(f"🔍 Testo estratto con OCR: '{testo_estratto.strip()}'")
            data_scadenza = self._estrai_e_normalizza_data(testo_estratto)
        except Exception as e:
            print(f"⚠️ Errore durante l'OCR: {e}")

        return Alimento(nome_alimento, sicurezza, data_scadenza)
