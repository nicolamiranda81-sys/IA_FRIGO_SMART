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
        cursor.execute("""
        SELECT nome, data_scadenza FROM alimenti
        WHERE data_scadenza IS NOT NULL AND data_scadenza != ''
        AND date(data_scadenza) <= date(?, '+7 days')
        AND date(data_scadenza) >= date(?)
        ORDER BY data_scadenza ASC
    """, (oggi, oggi))
        risultati = cursor.fetchall()            
        conn.close()                            
        return risultati

    def get_alimenti_per_ricette(self):
        conn, cursor = self._get_conn()         
        cursor.execute("SELECT DISTINCT nome FROM alimenti")  
        risultati = [row[0].lower() for row in cursor.fetchall()]     
        conn.close()                            
        return risultati

    def rimuovi_alimento(self, nome):
        conn, cursor = self._get_conn()          
        cursor.execute("""
        DELETE FROM alimenti WHERE id IN (
            SELECT id FROM alimenti WHERE LOWER(nome) = LOWER(?) LIMIT 1
        )
    """, (nome,))
        conn.commit()                            
        conn.close()      

    def svuota_database(self):
        conn, cursor = self._get_conn()
        cursor.execute("DELETE FROM alimenti")
        conn.commit()
        conn.close()
        print("🗑️ DB svuotato: pronto per la nuova scansione")

    def get_quantita_alimento(self, nome):
        conn, cursor = self._get_conn()
        cursor.execute("SELECT nome, COUNT(*) FROM alimenti WHERE LOWER(nome) = LOWER(?) GROUP BY nome", (nome,))
        risultato = cursor.fetchone()
        conn.close()
        return risultato                      

    def get_scadenza_alimento(self, nome):
        conn, cursor = self._get_conn()
        cursor.execute("""
            SELECT nome, data_scadenza FROM alimenti
            WHERE LOWER(nome) = LOWER(?)
            AND data_scadenza IS NOT NULL AND data_scadenza != ''
            LIMIT 1
        """, (nome,))
        risultato = cursor.fetchone()
        conn.close()
        return risultato

    def aggiorna_scadenza_alimento(self, alimento_id, nuova_data):
        """Aggiorna la data di scadenza di un singolo alimento dato il suo ID."""
        conn, cursor = self._get_conn()
        query = "UPDATE alimenti SET data_scadenza = ? WHERE id = ?"
        cursor.execute(query, (nuova_data, alimento_id))
        conn.commit()
        conn.close()
        print(f"✅ DB: Aggiornata scadenza per ID {alimento_id} a {nuova_data}")

    def get_Ricette(self):
        conn, cursor = self._get_conn()
        cursor.execute("""
            SELECT r.NOME, ar.NOME_ALIMENTO 
            FROM ALIMENTI_RICETTA ar
            JOIN RICETTA r ON r.COD_RICETTA = ar.COD_RICETTA
        """)
        
        table = cursor.fetchall()
        ricette_temp = {}
        
        for row in table:
            nome_ricetta = row[0]
            ingrediente = row[1]
            
            if nome_ricetta not in ricette_temp:
                ricette_temp[nome_ricetta] = []
                
            ricette_temp[nome_ricetta].append(ingrediente)
            
        conn.close()
        
        ricette_formato_target = {}
        
        for nome_ricetta, lista_ingredienti in ricette_temp.items():
            chiave_ingredienti = frozenset(lista_ingredienti)
            ricette_formato_target[chiave_ingredienti] = nome_ricetta
            
        return ricette_formato_target

# --- TEST DI FUNZIONAMENTO ---
if __name__ == "__main__":
    db = Database()
    test_alimento = Alimento(nome="Banana di Test", confidenza=99.9)
    db.aggiungi_alimento(test_alimento)