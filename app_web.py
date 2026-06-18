import cv2
import threading
import base64 

import numpy as np
import time
import os
import uuid
from flask import Flask, render_template, Response, request, jsonify
from riconoscitore_vocale import parla 
from rilevatore_Oggetti import trova_ritagli_con_sottrazione
from riconoscitore_alimenti import RiconoscitoreAlimenti
from database import Database
from Alimento import Alimento

# --- CONFIGURAZIONE DIALOGFLOW ---
# Imposta il percorso del file segreto scaricato da Google Cloud
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(BASE_DIR, "credenziali.json")
DIALOGFLOW_PROJECT_ID = "frigosmart-ejtr"  # Es: "frigo-smart-abcde"
DIALOGFLOW_LANGUAGE_CODE = "it"
SESSION_ID = str(uuid.uuid4()) # Crea una sessione univoca per la memoria dell'utente

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

# --- VARIABILI GLOBALI PER LIVE MODE WEB ---
ultimo_tempo_ia_web = 0
ultime_etichette_web = []

@app.route('/')
def index():
    """Carica la pagina HTML principale"""
    return render_template('index.html')

@app.route('/api/inventario', methods=['GET'])
def api_inventario():
    """Restituisce l'elenco degli alimenti nel database"""
    alimenti = db.get_tutti_alimenti()
    lista = [{"nome": row[0].capitalize(), "quantita": row[1]} for row in alimenti]
    return jsonify({'alimenti': lista})

@app.route('/api/svuota', methods=['POST'])
def api_svuota():
    """Svuota completamente il database"""
    db.svuota_database()
    return jsonify({'status': 'ok'})

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
    
    # 💬 Interroghiamo Dialogflow con il messaggio dell'utente!
    risposta = invia_a_dialogflow(messaggio_utente)
    
    # Se il volume è attivo nell'interfaccia, facciamo parlare l'assistente in background
    if volume_attivo:
        threading.Thread(target=parla, args=(risposta,)).start()

    return jsonify({'reply': risposta})

def genera_frame_live():
    """Cattura la webcam e trasmette il video in streaming con i rettangoli"""
    global ultimo_tempo_ia_web, ultime_etichette_web
    cap = cv2.VideoCapture(0)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            h, w = frame.shape[:2]
            nuova_larghezza = 800
            rapporto = nuova_larghezza / w
            frame = cv2.resize(frame, (nuova_larghezza, int(h * rapporto)))
            
            # Trova i contorni colorati
            ritagli = trova_ritagli_con_sottrazione(frame)
            tempo_corrente = time.time()
            
            # Interroga l'IA 1 volta al secondo per evitare scatti
            if tempo_corrente - ultimo_tempo_ia_web > 1.0:
                ultime_etichette_web.clear()
                for ritaglio_img, box in ritagli:
                    alimento = riconoscitore.riconosci(ritaglio_img)
                    if alimento and alimento.nome.lower() != 'nothing' and alimento.confidenza > 70:
                        ultime_etichette_web.append((box, f"{alimento.nome} ({int(alimento.confidenza)}%)"))
                ultimo_tempo_ia_web = tempo_corrente

            # Disegna rettangoli e testi
            for _, (x, y, w, h) in ritagli:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 100, 0), 2)
            for (x, y, w, h), etichetta in ultime_etichette_web:
                cv2.putText(frame, etichetta, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
            cv2.putText(frame, "LIVE MODE WEB", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # Converte il frame in JPEG per lo streaming HTTP
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        cap.release()

@app.route('/video_feed')
def video_feed():
    """Rotta che restituisce lo stream video continuo"""
    return Response(genera_frame_live(), mimetype='multipart/x-mixed-replace; boundary=frame')

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
            
        # ⚠️ FONDAMENTALE: Rimpiccioliamo l'immagine mantenendo le proporzioni originali!
        # Evita che le foto 16:9 dei cellulari vengano deformate compromettendo l'IA.
        h, w = frame.shape[:2]
        nuova_larghezza = 800
        rapporto = nuova_larghezza / w
        frame = cv2.resize(frame, (nuova_larghezza, int(h * rapporto)))
    except Exception as e:
        print(f"Errore decodifica immagine: {e}")
        return jsonify({'message': 'Errore nella decodifica dell\'immagine.'}), 400

    frame_elaborato = frame.copy()

    # 1. Trova i ritagli sull'immagine ricevuta dal telefono
    ritagli = trova_ritagli_con_sottrazione(frame)
    alimenti_trovati = []

    print(f"\n📸 Foto ricevuta dal cellulare!")
    print(f"🔎 Trovati {len(ritagli)} potenziali oggetti. Inizio Analisi IA...")

    # Svuotiamo il database dalle vecchie scansioni prima di inserire i nuovi risultati
    db.svuota_database()

    # 2. Riconosce ogni ritaglio tramite l'IA
    for indice, (ritaglio_img, (x, y, w, h)) in enumerate(ritagli, 1):
        print(f"🤖 Analisi oggetto {indice}/{len(ritagli)} in corso...")
        alimento = riconoscitore.riconosci(ritaglio_img)

        # Registriamo l'alimento rilevato nel database (incluso il cartone di uova come oggetto singolo)
        if alimento and alimento.nome.lower() != 'nothing' and alimento.confidenza > 70:
            db.aggiungi_alimento(alimento)
            alimenti_trovati.append(alimento.nome)
            
            # Disegniamo il rettangolo e l'etichetta sull'immagine elaborata
            etichetta = f"{alimento.nome} ({int(alimento.confidenza)}%)"
            cv2.rectangle(frame_elaborato, (x, y), (x + w, y + h), (0, 255, 0), 3)
            cv2.putText(frame_elaborato, etichetta, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # 3. Prepara la risposta
    if alimenti_trovati:
        risposta = f"Scansione completata! Ho trovato e salvato: {', '.join(alimenti_trovati)}."
    else:
        risposta = "Scansione terminata. Non ho riconosciuto nulla di noto."

    # 4. Codifichiamo l'immagine con i riquadri per inviarla al frontend
    _, buffer = cv2.imencode('.jpg', frame_elaborato)
    img_str = base64.b64encode(buffer).decode('utf-8')
    immagine_risultato_b64 = f"data:image/jpeg;base64,{img_str}"

    # Fa parlare l'assistente se il volume è attivo
    if volume_attivo:
        threading.Thread(target=parla, args=(risposta,)).start()

    return jsonify({'message': risposta, 'processedImage': immagine_risultato_b64})

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

    elif intent == 'ingredienti_ricetta':
        ricetta_richiesta = req['queryResult']['parameters'].get('ricetta', '').lower()
        ingredienti_necessari = []
        nome_ricetta_trovata = ""
        
        if ricetta_richiesta:
            # Cerchiamo la ricetta nel nostro dizionario
            for combo, nome_ricetta in RICETTE.items():
                # Controllo flessibile (se l'utente dice "la frittata" o solo "frittata")
                if ricetta_richiesta in nome_ricetta.lower() or nome_ricetta.lower() in ricetta_richiesta:
                    ingredienti_necessari = list(combo)
                    nome_ricetta_trovata = nome_ricetta
                    break
                
        if ingredienti_necessari:
            risposta = f"Per preparare {nome_ricetta_trovata} ti servono: {', '.join(ingredienti_necessari)}."
        else:
            risposta = f"Mi dispiace, non conosco gli ingredienti per {ricetta_richiesta if ricetta_richiesta else 'questa ricetta'}."

    else:
        risposta = "Non ho capito. Puoi chiedermi cosa hai nel frigo, cosa scade o cosa puoi cucinare!"

    return jsonify({"fulfillmentText": risposta})

if __name__ == '__main__':
    # host='0.0.0.0' permette a qualsiasi dispositivo nella rete Wi-Fi di collegarsi
    # use_reloader=False impedisce a Flask di creare un doppio processo che blocca la webcam
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)