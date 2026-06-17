import cv2
import threading
import base64
import numpy as np
import time
import os
import re
import uuid
from flask import Flask, render_template, Response, request, jsonify
from riconoscitore_vocale import parla
from rilevatore_Oggetti import trova_ritagli, conta_uova
from riconoscitore_alimenti import RiconoscitoreAlimenti
from database import Database

# --- CONFIGURAZIONE DIALOGFLOW ---
# Imposta il percorso del file segreto scaricato da Google Cloud
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\aless\OneDrive\Desktop\IA_FRIGO_SMART\credenziali.json"
DIALOGFLOW_PROJECT_ID = "frigosmart-ejtr"
DIALOGFLOW_LANGUAGE_CODE = "it"
SESSION_ID = str(uuid.uuid4()) # Crea una sessione univoca per la memoria dell'utente

app = Flask(__name__)

riconoscitore = RiconoscitoreAlimenti()
db = Database()

RICETTE = {
    frozenset(["uova", "latte"]): "frittata",
    frozenset(["banana", "yogurt"]): "frullato",
    frozenset(["carota", "cetriolo"]): "insalata di carote e cetrioli",
    frozenset(["carne rossa", "carota"]): "spezzatino di carne e carote",
    frozenset(["uova", "carne rossa"]): "uova con carne saltata",
    frozenset(["yogurt", "carota"]): "carote allo yogurt",
}

@app.route('/')
def index():
    """Carica la pagina HTML principale"""
    return render_template('index.html')

def invia_a_dialogflow(testo):
    """Invia il testo dell'utente a Dialogflow e recupera la risposta dell'Agente"""
    try:
        from google.cloud import dialogflow
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
        
        text_input = dialogflow.TextInput(text=testo, language_code=DIALOGFLOW_LANGUAGE_CODE)
        query_input = dialogflow.QueryInput(text=text_input)
        
        response = session_client.detect_intent(request={"session": session, "query_input": query_input})
        return response.query_result.fulfillment_text
    except Exception as e:
        print(f"Errore Dialogflow: {e}")
        return "Errore di connessione a Dialogflow. Hai configurato le credenziali e il Project ID?"

@app.route('/chat', methods=['POST'])
def chat():
    """Riceve i messaggi dalla pagina web e restituisce una risposta"""
    dati = request.get_json()
    messaggio_utente = dati.get('message', '')
    volume_attivo = dati.get('volumeOn', True)

    risposta = invia_a_dialogflow(messaggio_utente)

    if volume_attivo:
        threading.Thread(target=parla, args=(risposta,)).start()

    return jsonify({'reply': risposta})

@app.route('/scansiona', methods=['POST'])
def scansiona():
    """Riceve un'immagine dal dispositivo client, la decodifica e la scansiona"""
    dati = request.get_json() or {}
    volume_attivo = dati.get('volumeOn', True)
    immagine_b64 = dati.get('image', '')

    if not immagine_b64:
        return jsonify({'message': 'Errore: Nessuna immagine ricevuta dal dispositivo.'})

    try:
        if ',' in immagine_b64:
            immagine_b64 = immagine_b64.split(',')[1]
        img_bytes = base64.b64decode(immagine_b64)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            raise ValueError("Immagine non valida")

        frame = cv2.resize(frame, (800, 600))
    except Exception as e:
        return jsonify({'message': 'Errore nella decodifica dell\'immagine.'})

    ritagli = trova_ritagli(frame)
    alimenti_trovati = []

    print(f"\n📸 Foto ricevuta!")
    print(f"🔎 Trovati {len(ritagli)} potenziali oggetti. Inizio Analisi IA...")

    db.svuota_database()

    for indice, (ritaglio_img, box) in enumerate(ritagli, 1):
        x, y, w, h = box
        print(f"🤖 Analisi oggetto {indice}/{len(ritagli)} in corso...")
        alimento = riconoscitore.riconosci(ritaglio_img)
        riconosciuto = alimento and alimento.nome.lower() != 'nothing' and alimento.confidenza > 70

        if riconosciuto and alimento.nome.lower() == 'uova':
            sotto_box = conta_uova(ritaglio_img)
            if sotto_box:
                for (ux, uy, uw, uh) in sotto_box:
                    db.aggiungi_alimento(alimento)
                    alimenti_trovati.append(alimento.nome)
                    ax, ay = x + ux, y + uy
                    cv2.rectangle(frame, (ax, ay), (ax + uw, ay + uh), (76, 175, 80), 2)
                    cv2.putText(frame, "Uovo", (ax + 2, ay - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            else:
                db.aggiungi_alimento(alimento)
                alimenti_trovati.append(alimento.nome)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (76, 175, 80), 2)
                cv2.putText(frame, "Uova", (x + 2, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            continue
        elif riconosciuto:
            db.aggiungi_alimento(alimento)
            alimenti_trovati.append(alimento.nome)
            etichetta = f"{alimento.nome} {alimento.confidenza:.0f}%"
            colore = (76, 175, 80)
        else:
            etichetta = "non classificato"
            colore = (158, 158, 158)

        cv2.rectangle(frame, (x, y), (x + w, y + h), colore, 2)
        (tw, th), _ = cv2.getTextSize(etichetta, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x, y - th - 8), (x + tw + 6, y), colore, -1)
        cv2.putText(frame, etichetta, (x + 3, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    _, buffer = cv2.imencode('.jpg', frame)
    immagine_annotata = base64.b64encode(buffer).decode('utf-8')

    if alimenti_trovati:
        risposta = f"Scansione completata! Ho trovato e salvato: {', '.join(alimenti_trovati)}."
    else:
        risposta = "Scansione terminata. Non ho riconosciuto nulla di noto."

    if volume_attivo:
        threading.Thread(target=parla, args=(risposta,)).start()

    return jsonify({'message': risposta, 'immagine': f"data:image/jpeg;base64,{immagine_annotata}"})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Riceve le richieste da Dialogflow e interroga il database"""
    req = request.get_json()
    intent = req['queryResult']['intent']['displayName']

    if intent == 'cosa_ho_nel_frigo':
        alimenti = db.get_tutti_alimenti()
        if alimenti:
            lista = ", ".join([f"{row[1]} {row[0]}" for row in alimenti])
            risposta = f"Nel frigo hai: {lista}."
        else:
            risposta = "Il frigo è vuoto!"

    elif intent == 'cosa_scade_presto':
        scadenze = db.get_scadenze_vicine()
        if scadenze:
            lista = ", ".join([f"{row[0]} (scade il {row[1]})" for row in scadenze])
            risposta = f"Questi prodotti scadono presto: {lista}."
        else:
            risposta = "Nessun prodotto in scadenza."

    elif intent == 'cosa_posso_cucinare':
            ingredienti = set(i.lower() for i in db.get_alimenti_per_ricette())
            suggerimenti = []
            for combo, ricetta in RICETTE.items():
                if combo.issubset(ingredienti):
                    suggerimenti.append(ricetta)
            if suggerimenti:
                risposta = f"Puoi preparare: {', '.join(suggerimenti)}."
            else:
                risposta = "Non ho ricette per gli ingredienti che hai al momento."

    elif intent == 'ho_consumato_alimento':
        alimento = req['queryResult']['parameters'].get('alimento', '')
        if alimento:
            db.rimuovi_alimento(alimento)
            risposta = f"Ho rimosso {alimento} dal frigorifero."
        else:
            risposta = "Non ho capito quale alimento hai consumato."

    elif intent == 'quanti_ne_ho':
        alimento = req['queryResult']['parameters'].get('alimento', '')
        alimenti = db.get_tutti_alimenti()
        trovato = [row for row in alimenti if row[0].lower() == alimento.lower()]
        if trovato:
            risposta = f"Hai {trovato[0][1]} {trovato[0][0]} nel frigo."
        else:
            risposta = f"Non ho {alimento} nel frigo."

    elif intent == 'quando_scade_alimento':
        alimento = req['queryResult']['parameters'].get('alimento', '')
        risultato = db.get_scadenza_alimento(alimento)
        if risultato:
            risposta = f"{risultato[0]} scade il {risultato[1]}."
        else:
            risposta = f"Non ho informazioni sulla scadenza di {alimento}."

    else:
        risposta = "Non ho capito. Puoi chiedermi cosa hai nel frigo, cosa scade o cosa puoi cucinare!"

    return jsonify({"fulfillmentText": risposta})

if __name__ == '__main__':
    # host='0.0.0.0' permette a qualsiasi dispositivo nella rete Wi-Fi di collegarsi
    # use_reloader=False impedisce a Flask di creare un doppio processo che blocca la webcam
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)