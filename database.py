import sqlite3
from datetime import datetime
from Alimento import Alimento

class Database:
    def __init__(self, nome_db="frigo_smart.db"):
        # Connessione al database (se il file non esiste, verrà creato in automatico)
        self.conn = sqlite3.connect(nome_db, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.crea_tabella()

    def crea_tabella(self):
        # Creazione della tabella 'alimenti' se non è già presente
        query = """
        CREATE TABLE IF NOT EXISTS alimenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            confidenza REAL,
            data_scadenza TEXT,
            data_inserimento TEXT
        )
        """
        self.cursor.execute(query)
        self.conn.commit()

    def aggiungi_alimento(self, alimento):
        # Inserimento delle proprietà dell'oggetto Alimento nel database
        query = "INSERT INTO alimenti (nome, confidenza, data_scadenza, data_inserimento) VALUES (?, ?, ?, ?)"
        
        # Registriamo anche il momento esatto (timestamp) in cui la telecamera ha visto l'oggetto
        data_inserimento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        valori = (alimento.nome, alimento.confidenza, alimento.data_scadenza, data_inserimento)
        self.cursor.execute(query, valori)
        self.conn.commit()
        print(f"✅ DB: Salvato '{alimento.nome}' con successo!")

# --- TEST DI FUNZIONAMENTO ---
if __name__ == "__main__":
    db = Database()
    test_alimento = Alimento(nome="Banana di Test", confidenza=99.9)
    db.aggiungi_alimento(test_alimento)