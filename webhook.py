from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()
    intent = req['queryResult']['intent']['displayName']

    if intent == 'greeting':
        risposta = "Ciao! Sono FrigoSmart. Posso dirti cosa hai nel frigo, cosa sta per scadere e suggerirti ricette. Come posso aiutarti?"

    elif intent == 'cosa_ho_nel_frigo':
        risposta = "Ecco cosa hai nel frigo! (funzionalità in arrivo)"

    elif intent == 'cosa_scade_presto':
        risposta = "Questi prodotti scadono presto! (funzionalità in arrivo)"

    elif intent == 'cosa_posso_cucinare':
        risposta = "Ecco cosa puoi cucinare! (funzionalità in arrivo)"

    elif intent == 'ho_consumato_alimento':
        risposta = "Ho aggiornato il frigo! (funzionalità in arrivo)"

    elif intent == 'quanti_ne_ho':
        risposta = "Ecco la quantità! (funzionalità in arrivo)"

    elif intent == 'quando_scade_alimento':
        risposta = "Ecco la scadenza! (funzionalità in arrivo)"

    else:
        risposta = "Non ho capito. Puoi ripetere?"

    return jsonify({"fulfillmentText": risposta})

if __name__ == '__main__':
    app.run(port=5000)