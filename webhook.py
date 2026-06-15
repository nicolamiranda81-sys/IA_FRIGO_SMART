from flask import Flask, request, jsonify
from database import Database

app = Flask(__name__)
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

@app.route('/webhook', methods=['POST'])
def webhook():
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
    app.run(port=5000)