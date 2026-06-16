import cv2
import threading
import base64
import numpy as np
import time
from flask import Flask, render_template, Response, request, jsonify
from riconoscitore_vocale import parla
from rilevatore_Oggetti import trova_ritagli
from riconoscitore_alimenti import RiconoscitoreAlimenti
from database import Database

app = Flask(__name__)

riconoscitore = RiconoscitoreAlimenti()
db = Database()

RICETTE = {
    frozenset(["uova", "latte"]): "frittata",
    frozenset(["pomodoro", "mozzarella"]): "insalata caprese",
    frozenset(["banana", "yogurt"]): "frullato",
    frozenset(["carota", "lattuga"]): "insalata mista",
    frozenset(["uova", "burro"]): "uova strapazzate",
    frozenset(["mela verde", "yogurt"]): "Macedonia con yogurt",
    frozenset(["carne rossa", "cipolla bianca"]): "spezzatino",
}

@app.route('/')
def index():
    """Carica la pagina HTML principale"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Riceve i messaggi dalla pagina web e restituisce una risposta"""
    dati = request.get_json()
    messaggio_utente = dati.get('message', '')
    volume_attivo = dati.get('volumeOn', True)
    
    # PER ORA È UN PLACEHOLDER: Qui in futuro collegheremo l'IA vera!
    risposta = f"Hai detto: '{messaggio_utente}'. Presto potrò capirti per davvero!"
    
    # Se il volume è attivo nell'interfaccia, facciamo parlare l'assistente in background
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

    # Rimuove l'intestazione "data:image/jpeg;base64," e decodifica l'immagine per OpenCV
    try:
        if ',' in immagine_b64:
            immagine_b64 = immagine_b64.split(',')[1]
        img_bytes = base64.b64decode(immagine_b64)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            raise ValueError("Immagine non valida")
            
        # ⚠️ FONDAMENTALE: Rimpiccioliamo l'immagine prima di analizzarla!
        # Evita che l'IA si blocchi per decine di minuti su foto ad altissima risoluzione.
        frame = cv2.resize(frame, (800, 600))
    except Exception as e:
        return jsonify({'message': 'Errore nella decodifica dell\'immagine.'})

    # 1. Trova i ritagli sull'immagine ricevuta dal telefono
    ritagli = trova_ritagli(frame)
    alimenti_trovati = []

    print(f"\n📸 Foto ricevuta dal cellulare!")
    print(f"🔎 Trovati {len(ritagli)} potenziali oggetti. Inizio Analisi IA...")

    # 2. Riconosce ogni ritaglio tramite l'IA
    for indice, (ritaglio_img, _) in enumerate(ritagli, 1):
        print(f"🤖 Analisi oggetto {indice}/{len(ritagli)} in corso...")
        alimento = riconoscitore.riconosci(ritaglio_img)
        if alimento and alimento.nome.lower() != 'nothing' and alimento.confidenza > 70:
            db.aggiungi_alimento(alimento)
            alimenti_trovati.append(alimento.nome)

    # 3. Prepara la risposta
    if alimenti_trovati:
        risposta = f"Scansione completata! Ho trovato e salvato: {', '.join(alimenti_trovati)}."
    else:
        risposta = "Scansione terminata. Non ho riconosciuto nulla di noto."

    # Fa parlare l'assistente se il volume è attivo
    if volume_attivo:
        threading.Thread(target=parla, args=(risposta,)).start()

    return jsonify({'message': risposta})

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
        ingredienti = set(db.get_alimenti_per_ricette())
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
        scadenze = db.get_scadenze_vicine()
        trovato = [row for row in scadenze if row[0].lower() == alimento.lower()]
        if trovato:
            risposta = f"{trovato[0][0]} scade il {trovato[0][1]}."
        else:
            risposta = f"Non ho informazioni sulla scadenza di {alimento}."

    else:
        risposta = "Non ho capito. Puoi chiedermi cosa hai nel frigo, cosa scade o cosa puoi cucinare!"

    return jsonify({"fulfillmentText": risposta})

if __name__ == '__main__':
    # host='0.0.0.0' permette a qualsiasi dispositivo nella rete Wi-Fi di collegarsi
    # use_reloader=False impedisce a Flask di creare un doppio processo che blocca la webcam
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)