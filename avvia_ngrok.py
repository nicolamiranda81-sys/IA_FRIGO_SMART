from pyngrok import ngrok
import time

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