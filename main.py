import cv2
from rilevatore_Oggetti import trova_ritagli
from riconoscitore_alimenti import RiconoscitoreAlimenti
from database import Database
from cam import cam

riconoscitore = RiconoscitoreAlimenti()


db = Database()

print("Avvio Webcam...")
cap = cv2.VideoCapture(0)

while True:
    if not cam(cap, riconoscitore, db):
        break

cap.release()
cv2.destroyAllWindows()