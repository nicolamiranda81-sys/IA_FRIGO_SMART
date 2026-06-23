import cv2
import numpy as np
import pytesseract
from tensorflow.keras.models import load_model
from Alimento import Alimento
import re

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

        index_win = np.argmax(predict)
        nome = self.classi[index_win].strip()
        nome = nome[2:]
        sicurezza = predict[0][index_win]*100
        text  = pytesseract.image_to_string(immagine_cv2)
        pattern_data = r"\b(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})\b"
        date = re.findall(pattern_data,text)
        al = None
        if len(date)>0:
            al = Alimento(nome,sicurezza,date[0])
        else:
            al = Alimento(nome,sicurezza)
        return al 
