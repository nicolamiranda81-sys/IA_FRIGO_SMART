import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import cv2
from rilevatore_Oggetti import rileva_oggetti
from riconoscitore_alimenti import RiconoscitoreAlimenti

import numpy as np
from time import sleep
ra = RiconoscitoreAlimenti()


image = cv2.imread('realtest.jpeg')

cont=0
for obj in rileva_oggetti(image):
    cont+=1
    alimento = ra.riconosci(obj)
    print(alimento)
    

cv2.imshow('',image)
cv2.waitKey(0)
cv2.destroyAllWindows()


