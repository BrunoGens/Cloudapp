from flask import Flask, request
import os

app = Flask(__name__)

# VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "default_token")
VERIFY_TOKEN = os.getenv('WEBHOOK_VERIFY_TOKEN')
@app.route('/')
def home():
    return "Hello, World!"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return f"Webhook vérifié. Challenge: {challenge}", 200
        else:
            return "Token incorrect", 403
    return "Paramètres manquants", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
