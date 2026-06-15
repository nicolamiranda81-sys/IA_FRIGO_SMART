import sqlite3
from datetime import datetime
from Alimento import Alimento

class Database:
    def __init__(self, nome_db="frigo_smart.db"):
        # Connessione al database (se il file non esiste, verrà creato in automatico)
        self.nome_db = nome_db
        self.crea_tabella()

    def _get_conn(self):
        conn = sqlite3.connect(self.nome_db)
        return conn, conn.cursor()

    def crea_tabella(self):
        # Creazione della tabella 'alimenti' se non è già presente
        conn, cursor = self._get_conn()
        query = """
        CREATE TABLE IF NOT EXISTS alimenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            confidenza REAL,
            data_scadenza TEXT,
            data_inserimento TEXT
        )
        """
        cursor.execute(query)
        conn.commit()
        conn.close()  

    def aggiungi_alimento(self, alimento):
        # Inserimento delle proprietà dell'oggetto Alimento nel database
        conn, cursor = self._get_conn()
        query = "INSERT INTO alimenti (nome, confidenza, data_scadenza, data_inserimento) VALUES (?, ?, ?, ?)"
        
        # Registriamo anche il momento esatto (timestamp) in cui la telecamera ha visto l'oggetto
        data_inserimento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        valori = (alimento.nome, alimento.confidenza, alimento.data_scadenza, data_inserimento)
        cursor.execute(query, valori)
        conn.commit()
        conn.close()      
        print(f"✅ DB: Salvato '{alimento.nome}' con successo!")

    def get_tutti_alimenti(self):
        conn, cursor = self._get_conn()          
        cursor.execute("SELECT nome, COUNT(*) FROM alimenti GROUP BY nome")  
        risultati = cursor.fetchall()            
        conn.close()                             
        return risultati

    def get_scadenze_vicine(self):
        conn, cursor = self._get_conn()          
        oggi = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""SELECT ...""")         
        risultati = cursor.fetchall()            
        conn.close()                            
        return risultati

    def get_alimenti_per_ricette(self):
        conn, cursor = self._get_conn()         
        cursor.execute("SELECT DISTINCT nome FROM alimenti")  
        risultati = [row[0] for row in cursor.fetchall()]     
        conn.close()                            
        return risultati

    def rimuovi_alimento(self, nome):
        conn, cursor = self._get_conn()          
        cursor.execute("""DELETE ...""", (nome,)) 
        conn.commit()                            
        conn.close()      

    def get_quantita_alimento(self, nome):
        conn, cursor = self._get_conn()
        cursor.execute("SELECT nome, COUNT(*) FROM alimenti WHERE LOWER(nome) LIKE LOWER(?) GROUP BY nome", (f"%{nome[:5]}%",))
        risultato = cursor.fetchone()
        conn.close()
        return risultato                      

# --- TEST DI FUNZIONAMENTO ---
if __name__ == "__main__":
    db = Database()
    test_alimento = Alimento(nome="Banana di Test", confidenza=99.9)
    db.aggiungi_alimento(test_alimento)