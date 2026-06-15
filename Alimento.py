class Alimento:
    def __init__(self, nome, confidenza=0.0, data_scadenza=None):
        self.nome = nome
        self.confidenza = confidenza
        # La data di scadenza è nulla di default, potrà essere aggiornata successivamente
        self.data_scadenza = data_scadenza

    def __str__(self):
        """
        Metodo per stampare in modo leggibile l'oggetto nel terminale.
        """
        scadenza_str = self.data_scadenza if self.data_scadenza else "Non impostata (Null)"
        return (f"[OGGETTO ALIMENTO] => Nome: {self.nome} | "
                f"Affidabilità: {self.confidenza:.2f}% | Scadenza: {scadenza_str}")