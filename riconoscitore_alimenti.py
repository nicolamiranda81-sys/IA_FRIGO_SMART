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
        
        match = re.search(r'(\d{4})[-/.](\d{2})[-/.](\d{2})', testo)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        
        
        match = re.search(r'(\d{2})[-/.](\d{2})[-/.](\d{4})', testo)
        if match:
            
            return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
            
        return None

    def riconosci(self, immagine_cv2, debug_index=0):
        
        gray_image = cv2.cvtColor(immagine_cv2, cv2.COLOR_BGR2GRAY)

        
        h, w = gray_image.shape
        crop_top = gray_image[0:int(h * 0.25), :]       # banda superiore
        crop_bottom = gray_image[int(h * 0.75):h, :]    # banda inferiore

        
        for crop_region in [crop_top, crop_bottom, gray_image]:
            scale = 3
            ch, cw = crop_region.shape
            upscaled = cv2.resize(crop_region, (cw * scale, ch * scale), interpolation=cv2.INTER_CUBIC)
            
            _, binary = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            if np.mean(binary) < 127:
                binary = cv2.bitwise_not(binary)
            
            config = r'--psm 6 -c tessedit_char_whitelist=0123456789-/. '
            testo = pytesseract.image_to_string(binary, lang='ita', config=config)
            data_scadenza = self._estrai_e_normalizza_data(testo)
            
            if data_scadenza:  # appena trova una data valida, si ferma
                print(f"📅 Data trovata nella regione: '{data_scadenza}'")
                break

        
        img_resized = cv2.resize(immagine_cv2, (224, 224), interpolation=cv2.INTER_AREA)
        img_array = np.asarray(img_resized, dtype=np.float32).reshape(1, 224, 224, 3)
        img_normalized = (img_array / 127.5) - 1

        predict = self.modello_tm.predict(img_normalized)
        index_win = np.argmax(predict)
        nome_alimento = self.classi[index_win].strip().split(" ", 1)[1]
        sicurezza = predict[0][index_win] * 100

        
        data_scadenza = None
        try:
            
            cv2.imwrite(f"debug_originale_{debug_index}.jpg", immagine_cv2)
            print(f"📐 Dimensioni immagine ricevuta: {immagine_cv2.shape}")

            gray_image = cv2.cvtColor(immagine_cv2, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(f"debug_gray_{debug_index}.jpg", gray_image)

            
            scale = 3
            h, w = gray_image.shape
            upscaled = cv2.resize(gray_image, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)
            cv2.imwrite(f"debug_upscaled_{debug_index}.jpg", upscaled)

            
            _, binary = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        
            mean_val = np.mean(binary)
            print(f"📊 Luminosità media immagine binaria: {mean_val:.1f} (se <127 verrà invertita)")
            if mean_val < 127:
                binary = cv2.bitwise_not(binary)

            cv2.imwrite(f"debug_binary_{debug_index}.jpg", binary)

            
            testo_raw = pytesseract.image_to_string(binary, lang='ita')
            print(f"🔍 Testo RAW (senza filtri): '{testo_raw.strip()}'")

            
            config = r'--psm 6 -c tessedit_char_whitelist=0123456789-/. '
            testo_estratto = pytesseract.image_to_string(binary, lang='ita', config=config)
            

            data_scadenza = self._estrai_e_normalizza_data(testo_estratto)
            

        except Exception as e:
            pass

        return Alimento(nome_alimento, sicurezza, data_scadenza)