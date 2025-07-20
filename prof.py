from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, World!"



  
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            message = f"Webhook vérifié avec succès. Challenge: {challenge}"
            print(message)
            return f"<html><body><h1>{message}</h1></body></html>", 200
        else:
            message = "Échec de vérification du webhook : token incorrect."
            print(message)
            return f"<html><body><h1>{message}</h1></body></html>", 403
    else:
        message = "Paramètres manquants dans la requête."
        print(message)
        return f"<html><body><h1>{message}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
