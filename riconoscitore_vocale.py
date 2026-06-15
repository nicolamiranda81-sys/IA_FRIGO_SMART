import speech_recognition as sr
import pyttsx3
import time

# Inizializzazione globale del motore vocale
motore_tts = pyttsx3.init()

# Cerchiamo di impostare una voce italiana, se disponibile nel sistema
voci = motore_tts.getProperty('voices')
for voce in voci:
    if 'it' in voce.languages or 'italian' in voce.name.lower():
        motore_tts.setProperty('voice', voce.id)
        break

def parla(testo):
    """Legge ad alta voce il testo passato come argomento."""
    print(f"🗣️ Assistente: {testo}")
    motore_tts.say(testo)
    motore_tts.runAndWait()

def ascolta():
    """Si mette in ascolto dal microfono e ritorna la stringa riconosciuta."""
    riconoscitore = sr.Recognizer()
    
    with sr.Microphone() as sorgente:
        print("\n🎤 In ascolto... (parla ora)")
        # Calibra il microfono per il rumore di fondo (1 secondo)
        riconoscitore.adjust_for_ambient_noise(sorgente, duration=1)
        riconoscitore.dynamic_energy_threshold = True
        
        try:
            # Impostiamo un timeout massimo di 8 secondi (così non si blocca all'infinito se la VM è muta)
            audio = riconoscitore.listen(sorgente, timeout=8, phrase_time_limit=10)
            print("⏳ Elaborazione in corso...")
            
            # Usa il riconoscimento gratuito di Google
            testo_riconosciuto = riconoscitore.recognize_google(audio, language="it-IT")
            print(f"👤 Tu hai detto: '{testo_riconosciuto}'")
            return testo_riconosciuto
            
        except sr.WaitTimeoutError:
            print("❌ Nessun suono rilevato entro il tempo limite.")
        except sr.UnknownValueError:
            print("❌ Non ho capito cosa hai detto.")
        except sr.RequestError as e:
            print(f"❌ Errore di connessione a Internet/Servizio Google: {e}")
            
    return None

# TEST
if __name__ == "__main__":
    parla("Ciao! Sono il tuo assistente vocale. Dimmi qualcosa.")
    
    # Breve pausa per evitare che Linux blocchi l'audio passando da uscita a ingresso
    time.sleep(0.5) 

    frase = ascolta()
    if frase:
        parla(f"Ho sentito che hai detto: {frase}")
    else:
        parla("Non ho sentito nulla, chiudo il programma.")