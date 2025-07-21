# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 21:46:53 2024

@author: Bruno
"""

from dotenv import load_dotenv
import openai
import os
from flask import Flask, request, jsonify
import requests
from gtts import gTTS
from io import BytesIO
from datetime import datetime
import sys
from google.cloud import storage
import logging

sys.stdout.reconfigure(line_buffering=True)

BUCKET_NAME = "prof_lang_memory_bucket"
FICHIER = "FichierTest.txt"

def upload_text(content, fichier):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(fichier)
    blob.upload_from_string(content)

def download_text(fichier):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(fichier)
    if not blob.exists():
        return ""
    return blob.download_as_text()

def append_text_to_file(fichier: str, new_content: str):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(fichier)

    # Télécharger l'ancien contenu s'il existe
    if blob.exists():
        old_content = blob.download_as_text()
    else:
        old_content = ""

    # Ajouter le nouveau contenu à la fin
    updated_content = old_content + new_content

    # Réécrire le fichier avec le contenu mis à jour
    blob.upload_from_string(updated_content)
# Charger les variables d'environnement depuis le fichier .env
load_dotenv()


# Variables globales provenant des variables d'environnement
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHATSAPP_API_TOKEN  = os.getenv("WHATSAPP_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
business_phone_number_id = os.getenv("PHONE_NUMBER_ID")

WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages"


#rep = "C:/Users/Bruno/OneDrive/0Bruno - DigUp/00 -  DigUp/04 - eCommerce/07 - Automatisation produits/02 - Product files/"
def sauvegarder_audio(texte, chemin_fichier):
    # Créer l'audio en utilisant gTTS avec le texte fourni et la langue italienne
    tts = gTTS(text=texte, lang='it')  # Utilisez 'fr' pour le français si besoin
    # Sauvegarder le fichier audio en format MP3
    tts.save(chemin_fichier)
    print(f"Le fichier audio a été enregistré à l'emplacement : {chemin_fichier}")


# Configuration OpenAI
openai.api_key = OPENAI_API_KEY

# Flask app
app = Flask(__name__)

# Logger basique (améliorable)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def mark_as_read(message_id):
    access_token = WHATSAPP_API_TOKEN  # Remplacez par votre token d'accès
    url = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print("Message marqué comme lu avec succès.")
    else:
        print(f"Erreur lors du marquage du message comme lu : {response.status_code} - {response.text}")

# Dans la fonction webhook, après avoir extrait `phone_number` et `message_id` depuis `data`
# Remplacez `phone_number_id` et `access_token` par vos identifiants


def get_audio_url(media_id):
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        audio_data = response.json()
        return audio_data.get("url")
    else:
        print(f"Erreur lors de la récupération de l'URL audio: {response.status_code}")
        return None

def envoyer_reponse_whatsapp(numero, message, audio_content=None):
    headers = {
        'Authorization': f'Bearer {WHATSAPP_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Envoi de la transcription texte
    if message:
        data = {
            "messaging_product": "whatsapp",
            "to": numero,
            "text": {"body": message}
        }
        requests.post(WHATSAPP_API_URL, headers=headers, json=data)

    # Envoi de la réponse audio
    if audio_content:
        files = {
            'file': ('reponse.mp3', audio_content, 'audio/mp3')
        }
        data = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "audio"
        }
        requests.post(WHATSAPP_API_URL, headers=headers, files=files, data=data)
        
def envoyer_texte_whatsapp(numero, message):
    """
    Envoie un message texte via WhatsApp.
    
    Args:
    - numero (str): Le numéro de téléphone du destinataire.
    - message (str): Le texte du message à envoyer.
    """
    headers = {
        'Authorization': f'Bearer {WHATSAPP_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "text": {"body": message}
    }
    response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)
    # response.raise_for_status()  # Vérifier que la requête a réussi


#audio_url = "C:/Users/Bruno/OneDrive/0Bruno - DigUp/00 -  DigUp/04 - eCommerce/07 - Automatisation produits/02 - Product files/-Italiano-2024-11-08_18-56-23.mp3"

def uploader_audio_sur_facebook(audio_content):
    url_upload = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/media"
    headers = {
        'Authorization': f'Bearer {WHATSAPP_API_TOKEN}'
    }
    files = {
        'file': ('contenuaudio.mp3', BytesIO(audio_content), 'audio/mpeg')  # Utiliser BytesIO pour simuler un fichier
    }
    data = {
        "messaging_product": "whatsapp",
        "type": "audio"
    }

    response = requests.post(url_upload, headers=headers, files=files, data=data)

    if response.status_code == 200:
        media_id = response.json().get("id")
        print("Fichier audio uploadé avec succès, ID du média:", media_id)
        return media_id
    else:
        print("Erreur lors de l'uploading du fichier audio.")
        print("Code d'erreur:", response.status_code)
        print("Réponse de l'API:", response.json())
        return None


#Commentaire 
def envoyer_audio_whatsapp_par_media_id(numero, media_id):
    headers = {
        'Authorization': f'Bearer {WHATSAPP_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "audio",
        "audio": {
            "id": media_id
        }
    }

    response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        print("Message audio envoyé avec succès.")
    else:
        print("Erreur lors de l'envoi du message audio.")
        print("Code d'erreur:", response.status_code)
        print("Réponse de l'API:", response.json())


def envoyer_audio_whatsapp(recipient_number, audio_content):
    # Appel de la fonction pour télécharger le fichier audio
    media_id = uploader_audio_sur_facebook(audio_content)
    # Vérifiez si l'upload a réussi avant d'envoyer le message
    if media_id:
        envoyer_audio_whatsapp_par_media_id(recipient_number, media_id)


# Configurer les points d'accès API
WHISPER_ENDPOINT = 'https://api.openai.com/v1/audio/transcriptions'
CHATGPT_ENDPOINT = 'https://api.openai.com/v1/completions'
# Audio_path = 'C:/Users/Bruno/OneDrive/0Bruno - DigUp/00 -  DigUp/04 - eCommerce/07 - Automatisation produits/RECORDING_20230529_144958582.m4a.mp3'


        
def transcribe_audio_from_url(file_url):
    # Étape 1 : Télécharger le fichier audio via l'API de WhatsApp
    headers_whatsapp = {
        'Authorization': f'Bearer {WHATSAPP_API_TOKEN}'
    }
    
    # Effectuer la requête pour récupérer le fichier audio depuis l'URL
    response_audio = requests.get(file_url, headers=headers_whatsapp)
    
    if response_audio.status_code != 200:
        raise Exception(f"Erreur de téléchargement du fichier audio: {response_audio.text}")
    
    # Sauvegarder temporairement le fichier audio
    with open("audio_temp.ogg", "wb") as audio_file:
        audio_file.write(response_audio.content)
    
    # Étape 2 : Transcrire le fichier audio en utilisant l'API de transcription
    headers_openai = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
    }
    files = {
        'file': open("audio_temp.ogg", 'rb'),
        'model': (None, 'whisper-1')
    }
    
    response_transcription = requests.post(WHISPER_ENDPOINT, headers=headers_openai, files=files)
    
    # Supprimer le fichier temporaire après la transcription
#    os.remove("audio_temp.ogg")
    
    # Vérifier le succès de la transcription et retourner le texte
    if response_transcription.status_code == 200:
        return response_transcription.json()['text']
    else:
        raise Exception(f"Erreur de transcription: {response_transcription.text}")

def analyze_caption_with_chatgpt(prompt, content=""):

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": content},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500,
        n=1,
        stop=None,
        temperature=0.7,
    )
    # print("retour chatgpt: ")
    # print(response.choices[0].message.content.strip())
    ret = response.choices[0].message.content.strip()
    #print(ret)
    return ret


def conversation_italien(audio_url):


    transcription_text = transcribe_audio_from_url(audio_url)
    
    print(f"Transcription de l'audio : {transcription_text}")
    
    
    prompt = f"Agis comme un professeur d'italien. ton but est d'avoir une conversation avec moi, c'est-à-dire qu'il faut que tu trouves des sujest de conversation en lien avec ce que je dis : Réponds toujours en italien, et corrige les principales erreurs que tu détectes dans mes messages. Message : {transcription_text}"

    italian_response = analyze_caption_with_chatgpt(prompt)    

    print(f"Réponse du professeur d'italien : {italian_response}")
    
    # Étape 4 : Générer la réponse audio en italien avec gTTS
    tts = gTTS(text=italian_response.replace('*',''), lang='it')  # Langue 'it' pour l'italien
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)  # Écriture directe dans le buffer
    audio_buffer.seek(0)  # Revenir au début du buffer pour la lecture

    # chemin_fichier = "FichierTest" # Spécifiez ici l'emplacement souhaité  
    print(f"Contenu fichier Test : {download_text(FICHIER)}")
    text = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')} - {italian_response}"  # Spécifiez ici l'emplacement souhaité
    print(f"Ajout du texte : {text}")
    append_text_to_file(FICHIER, text)
    
    print(f"nouveau Contenu fichier Test : {download_text(FICHIER)}")

    # print(f"Le fichier audio a été enregistré à l'emplacement : {chemin_fichier}")
    
    # Retourner la transcription et le contenu audio généré
    return italian_response, audio_buffer.getvalue()

# Route pour la racine
@app.route("/", methods=["GET"])
def home():
    return "Bienvenue sur le webhook de l'API WhatsApp !", 200

VERIFY_TOKEN = "ABCD"  


  
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


    
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        
        # Vérifier si 'messages' est présent dans le payload
        if 'messages' not in data['entry'][0]['changes'][0]['value']:
            print("Pas de 'messages' dans la structure 'value', événement ignoré.")
#            print(f"Data : {data}")
            return "Événement ignoré", 200

        # Vérifier si la structure des données contient les clés nécessaires
        if 'entry' not in data or not data['entry'][0].get('changes'):
            print("Structure inattendue du webhook.")
            return "Événement ignoré", 200

        # Vérifier si 'messages' ou 'statuses' est présent dans la structure attendue
        # Filtrer les messages de statut
        if 'statuses' in data['entry'][0]['changes'][0]['value']:
            print("Événement de statut reçu, ignorer...")
            return "Événement ignoré", 200  # Sortir directement pour ignorer cet événement

        try:
            phone_number = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
            print(f"Numéro de téléphone: {phone_number}")
        except Exception as a:
            print(f"Exception {a} : payload was {data}")
            return "Erreur dans les données du message", 400
         
        try: 
            message_id = data['entry'][0]['changes'][0]['value']['messages'][0]['id']
            print(f"Id du message: {message_id}")
            mark_as_read( message_id)
        except Exception as g:
            print(f"Exception {g} : unable to read message's id")

        try:
            message = data['entry'][0]['changes'][0]['value']['messages'][0]
            audio_url = None
            # Vérifier que le type du message est bien "audio"
            if message.get('type') == 'audio':
                audio_id = message['audio']['id']
                print(f"ID de l'audio: {audio_id}")
                
                # Utiliser l'ID pour obtenir l'URL de l'audio
                audio_url = get_audio_url(audio_id)        
        except KeyError:
            print("Aucun audio trouvé dans le message.")
            audio_url = None
            # Transcrire et générer une réponse audio et textuelle
        
        if audio_url != None:
            reponse_italien, audio_response = conversation_italien(audio_url)
            
            # Envoyer la réponse textuelle et audio
            # envoyer_reponse_whatsapp(phone_number, transcription, audio_response)
            envoyer_texte_whatsapp(phone_number, reponse_italien)
            envoyer_audio_whatsapp(phone_number, audio_response)
            
            
        # print(data)
            
        return jsonify({"status": "message envoyé"}), 200

    except Exception as e:
        print(f"Erreur lors du traitement des données : {e}")
        import traceback
        traceback.print_exc()
        return "Erreur interne", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

