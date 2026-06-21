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

        index_win = np.argmax(predict)
        nome = self.classi[index_win].strip()
        sicurezza = predict[0][index_win]*100
        return nome,sicurezza