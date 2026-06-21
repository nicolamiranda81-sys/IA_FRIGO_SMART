import cv2
import numpy as np
from tensorflow.keras.models import load_model

class RiconoscitoreAlimenti:
    def __init__(self):
        self.modello_tm = load_model("keras_model.h5", compile=False)
        with open("labels.txt", "r") as f:
            self.classi = f.readlines()

    def riconosci(self, immagine_cv2):
        img_tm = cv2.resize(immagine_cv2,(224,224),interpolation=cv2.INTER_AREA)
        img_tm = np.asarray(img_tm,dtype=np.float32).reshape(1,224,224,3)
        img_tm = (img_tm/127.5)-1

        predict = self.modello_tm.predict(img_tm)

<<<<<<< HEAD
        index_win = np.argmax(predict)
        nome = self.classi[index_win].strip()
        sicurezza = predict[0][index_win]*100
        return nome,sicurezza
=======
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
>>>>>>> 16bb696b658e5b36683926b1534510c9374e96fd
