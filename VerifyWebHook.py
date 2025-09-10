# -*- coding: utf-8 -*-
"""
Created on Sun Jul 20 16:01:18 2025

@author: Bruno
"""

from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "ABCD"  # Assurez-vous que cela correspond à votre token de vérification

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("Webhook vérifié avec succès")
            return challenge, 200, {'Content-Type': 'text/plain'}  # Assurez-vous de renvoyer le challenge tel quel
        else:
            print("Échec de vérification du webhook")
            return "Forbidden", 403
    else:
        print("Paramètres manquants dans la requête")
        return "Bad Request", 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
