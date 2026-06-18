import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "frigo_smart.db"

def genera_data_scadenza_vicina():
    """
    Genera una data casuale tra oggi e i prossimi 7 giorni.
    """
    giorni = random.randint(0, 7)
    data = datetime.now() + timedelta(days=giorni)
    return data.strftime("%Y-%m-%d")

def aggiorna_scadenze():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome FROM alimenti")
    alimenti = cursor.fetchall()

    if not alimenti:
        print("⚠️ Nessun alimento trovato nel database.")
        conn.close()
        return

    print("📅 Aggiornamento scadenze...\n")

    for id_alimento, nome in alimenti:
        data_scadenza = genera_data_scadenza_vicina()

        cursor.execute("""
            UPDATE alimenti
            SET data_scadenza = ?
            WHERE id = ?
        """, (data_scadenza, id_alimento))

        print(f"✅ {nome} -> {data_scadenza}")

    conn.commit()
    conn.close()

    print("\n🎉 Aggiornamento completato!")

if __name__ == "__main__":
    aggiorna_scadenze()