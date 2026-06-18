from pyngrok import ngrok
import time
ngrok.kill()
# Imposta qui il tuo authtoken preso dalla dashboard di ngrok
ngrok.set_auth_token("3FDiQN2ktO5QoL6fSZVzqwj2iZ1_7dDWCWtTGzmnRSNUZeZoL")

tunnel = ngrok.connect(5000)
print("=" * 50)
print(f"URL NGROK: {tunnel.public_url}/webhook")
print("Copia questo URL in Dialogflow Fulfillment")
print("NON chiudere questo terminale!")
print("=" * 50)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ngrok.disconnect(tunnel.public_url)
    print("Tunnel chiuso.")