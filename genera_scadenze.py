import sqlite3
import random
from datetime import datetime, timedelta
import os

def main():
    # Percorso del database
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "frigo_smart.db")
    
    # Connessione al database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Recupera tutti gli alimenti presenti
    cursor.execute("SELECT id, nome FROM alimenti")
    alimenti = cursor.fetchall()
    
    if not alimenti:
        print("⚠️ Il database è vuoto! Fai prima una scansione dalla web app o fotocamera.")
        return
        
    oggi = datetime.now()
    
    # Aggiorna ogni alimento con una data di scadenza casuale (tra 1 e 10 giorni da oggi)
    for id_alimento, nome in alimenti:
        giorni_rimanenti = random.randint(1, 10)
        nuova_scadenza = (oggi + timedelta(days=giorni_rimanenti)).strftime("%Y-%m-%d")
        
        cursor.execute("UPDATE alimenti SET data_scadenza = ? WHERE id = ?", (nuova_scadenza, id_alimento))
        print(f"✅ {nome} aggiornato -> Nuova Scadenza: {nuova_scadenza} (tra {giorni_rimanenti} giorni)")
        
    conn.commit()
    conn.close()
    print("\n🎉 Tutte le date di scadenza sono state generate e salvate nel database!")

if __name__ == "__main__":
    main()