import cv2
import numpy as np
import os
from PIL import Image, ImageOps

# 1. FORZIAMO TENSORFLOW A USARE LA VERSIONE COMPATIBILE CON TEACHABLE MACHINE (Keras 2 / Legacy)
os.environ['TF_USE_LEGACY_KERAS'] = '1'
# Disabilitiamo i log di avviso di TensorFlow per avere un terminale più pulito
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import tensorflow as tf
from Alimento import Alimento

class RiconoscitoreAlimenti:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.percorso_modello = os.path.join(base_dir, "keras_model.h5")
        self.percorso_labels = os.path.join(base_dir, "labels.txt")
        
        try:
            self.modello = tf.keras.models.load_model(self.percorso_modello, compile=False)
            with open(self.percorso_labels, "r", encoding="utf-8") as file_labels:
                self.nomi_classi = file_labels.readlines()
            
            print("Esecuzione 'warm-up' del modello (potrebbe richiedere qualche secondo)...")
            immagine_dummy = np.zeros((1, 224, 224, 3), dtype=np.float32)
            self.modello.predict(immagine_dummy, verbose=0)
            
            print("Modello IA caricato e pronto con successo!")
        except Exception as e:
            print("\n" + "="*60)
            print("🚨 ATTENZIONE: MANCA UNA LIBRERIA FONDAMENTALE 🚨")
            print("TensorFlow ha bloccato il modello per incompatibilità di versione.")
            print("Per risolvere DEFINITIVAMENTE questo problema, apri un")
            print("nuovo terminale e digita esattamente questo comando:")
            print("\n    pip3 install tf-keras\n")
            print("Una volta installato, riavvia questo script.")
            print("="*60 + "\n")
            self.modello = None

    def riconosci(self, immagine_cv2):
        if self.modello is None or immagine_cv2 is None or immagine_cv2.size == 0:
            return None

        immagine_rgb = cv2.cvtColor(immagine_cv2, cv2.COLOR_BGR2RGB)

        pil_image = Image.fromarray(immagine_rgb).convert("RGB")

        pil_image = ImageOps.fit(
            pil_image,
            (224, 224),
            Image.Resampling.LANCZOS
        )

        immagine_array = np.asarray(pil_image)
        immagine_array = (immagine_array.astype(np.float32) / 127.5) - 1

        data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
        data[0] = immagine_array

        previsione = self.modello.predict(data, verbose=0)

        indice_classe = np.argmax(previsione)
        nome_classe_grezzo = self.nomi_classi[indice_classe].strip()
        nome_pulito = nome_classe_grezzo.split(" ", 1)[1] if " " in nome_classe_grezzo else nome_classe_grezzo

        if nome_pulito.lower() == "affettati":
            nome_pulito = "Yogurt"
        elif nome_pulito.lower() == "yogurt":
            nome_pulito = "Affettati"
            
        punteggio_confidenza = previsione[0][indice_classe] * 100

        return Alimento(nome=nome_pulito, confidenza=punteggio_confidenza)