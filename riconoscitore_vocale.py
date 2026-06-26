import speech_recognition as sr
import pyttsx3
import time

motore_tts = pyttsx3.init()

voci = motore_tts.getProperty('voices')
for voce in voci:
    if 'it' in voce.languages or 'italian' in voce.name.lower():
        motore_tts.setProperty('voice', voce.id)
        break

def parla(testo):
    """Legge ad alta voce il testo passato come argomento."""
    motore_tts.say(testo)
    motore_tts.runAndWait()

def ascolta():
    """Si mette in ascolto dal microfono e ritorna la stringa riconosciuta."""
    riconoscitore = sr.Recognizer()
    
    with sr.Microphone() as sorgente:
        
        riconoscitore.adjust_for_ambient_noise(sorgente, duration=1)
        riconoscitore.dynamic_energy_threshold = True
        
        try:
            # Impostiamo un timeout massimo di 8 secondi (così non si blocca all'infinito se la VM è muta)
            audio = riconoscitore.listen(sorgente, timeout=8, phrase_time_limit=10)
            print("⏳ Elaborazione in corso...")
            
            # Usa il riconoscimento gratuito di Google
            testo_riconosciuto = riconoscitore.recognize_google(audio, language="it-IT")
            return testo_riconosciuto
            
        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            pass
            
    return None
