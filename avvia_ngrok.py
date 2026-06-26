from pyngrok import ngrok
import time
ngrok.kill()
ngrok.set_auth_token("3EM0fRPBQq6349tDiICNxtebkgn_7EF648wALwmbUWoeP21DE")

tunnel = ngrok.connect(5000)

print(f"URL NGROK: {tunnel.public_url}/webhook")


try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ngrok.disconnect(tunnel.public_url)
    print("Tunnel chiuso.")