from flask import Flask, request, jsonify
from database import Database

app = Flask(__name__)
db = Database()



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
    app.run(port=5000)