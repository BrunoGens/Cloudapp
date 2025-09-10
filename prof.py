# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 21:46:53 2024

@author: Bruno
"""

import openai
#from OpenAI_Completion import analyze_caption_with_chatgpt
from flask import Flask, request, jsonify
import requests
from io import BytesIO
from datetime import datetime, timedelta
import os
import json
#import azure.cognitiveservices.speech as speechsdk
from google.cloud import texttospeech
from FichesConversation import FichesConvers
import subprocess
import uuid
import traceback
import tempfile
import sys
from google.cloud import storage


sys.stdout.reconfigure(line_buffering=True)



MaintenanceMode=False
MaintenanceAutorized = ['33633861297']

Messages_id=[]

rep = "/Product/"
#rep = "Users/Bruno/OneDrive/0Bruno - DigUp/00 -  DigUp/04 - eCommerce/07 - Automatisation produits/02 - Product files/"
# Chat_save_dir = 'C:/Users/Bruno/OneDrive/0Bruno - DigUp/00 -  DigUp/04 - eCommerce/07 - Automatisation produits/03 - Chats/'
Chat_save_dir = '/Chat/'

memory = {}

BUCKET_NAME = "prof_lang_memory_bucket"
FICHIER = "FichierTest.txt"




OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHATSAPP_API_TOKEN  = os.getenv("WHATSAPP_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
business_phone_number_id = os.getenv("PHONE_NUMBER_ID")

WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages"

# Initialiser l'API OpenAI
openai.api_key = OPENAI_API_KEY


# === CONFIGURATION AZURE (deprecated)===
SPEECH_KEY = os.getenv("SPEECH_KEY")
SERVICE_REGION = "francecentral"  # ex: "westeurope"


help_text = "Bonjour ! Je suis un chatbot conçu pour vous aider à pratiquer votre langue. Voici comment je fonctionne : \n \
- Envoyez-moi des messages audio (vocaux) dans la langue que vous apprenez.\n \
- Je reformule vos phrases et vous aider à améliorer votre expression.\n \
- Je vous renvoie une nouvelle question pour prolonger la conversation \n\n \
Voici quelques commandes supplémentaires que vous pouvez utiliser : \n \
    * 👅 tapez *.italien*, ou *.français*, pour définir /changer la langue d'apprentissage (aussi disponible : anglais, allemand, espagnol, ou chinois) \n \
    * 📢 tapez *.audio_response_on* Si vous désirez obtenir ma réponse aussi sous forme de vocal (en + du texte),  (*.audio_response_off* pour désactiver) \n \
    * 👨‍🏫 tapez *.summary* pour obtenir une synthèse de vos efforts d'apprentissage. \n \
    * 📜 tapez *.story* pour créer une histoire adaptée à votre niveau de compréhension (travail compréhension orale) \n \
    * ❔ tapez *.help* pour afficher de nouveau cet aide"

langues = {
    'allemand': {'langue_apprentissage': 'de', 'langue_nom': 'allemand', 'code_langue': 'de-DE', 'google_language_code': 'de-DE', 'google_voice_name': 'de-DE-Wavenet-B','catchup_phrase': 'Hallo, wie geht es dir? Wie sind deine letzten Tage verlaufen? [écrivez "stop" pour désactiver ces messages]'},
    'italien': {'langue_apprentissage': 'it', 'langue_nom': 'italien', 'code_langue': 'it-IT', 'google_language_code': 'it-IT', 'google_voice_name': 'it-IT-Wavenet-C','catchup_phrase': 'Ciao, come stai? Come sono andati i tuoi ultimi giorni? [écrivez "stop" pour désactiver ces messages]'},
    'anglais': {'langue_apprentissage': 'en', 'langue_nom': 'anglais', 'code_langue': 'en-UK', 'google_language_code': 'en-GB', 'google_voice_name': 'en-GB-Wavenet-A','catchup_phrase': 'Hello, how are you? How have your last few days been? [écrivez "stop" pour désactiver ces messages]'},
    'espagnol': {'langue_apprentissage': 'es', 'langue_nom': 'espagnol', 'code_langue': 'es-ES', 'google_language_code': 'es-ES', 'google_voice_name': 'es-ES-Wavenet-A','catchup_phrase': 'Hola, ¿cómo estás? ¿Cómo han sido tus últimos días? [écrivez "stop" pour désactiver ces messages]'},
    'chinois': {'langue_apprentissage': 'zh', 'langue_nom': 'chinois', 'code_langue': 'zh-CN', 'google_language_code': 'cmn-CN', 'google_voice_name': 'cmn-CN-Wavenet-A','catchup_phrase': '你好，你怎么样？你这几天过得怎么样？ [écrivez "stop" pour désactiver ces messages]'},
    'français': {'langue_apprentissage': 'fr', 'langue_nom': 'français', 'code_langue': 'fr-FR', 'google_language_code': 'fr-FR', 'google_voice_name': 'fr-FR-Wavenet-B','catchup_phrase': 'Bonjour, comment vas-tu ? Comment se sont passés tes derniers jours ? [écrivez "stop" pour désactiver ces messages]'}
}

reference_texts = {
    'en-US': "The quick brown fox jumps over the lazy dog near the river bank at sunset",
    'fr-FR': "Le vif renard brun saute par-dessus le chien paresseux près de la berge au coucher du soleil",
    'en-UK': "The quick brown fox jumps over the lazy dog near the river bank at sunset",
    'it-IT': "La veloce volpe marrone salta sopra il cane pigro vicino alla riva al tramonto",
    'es-ES': "El rápido zorro marrón salta sobre el perro perezoso cerca de la orilla al atardecer",
    'de-DE': "Der flinke braune Fuchs springt über den faulen Hund in der Nähe des Flussufers bei Sonnenuntergang",
    'zh-CN': "敏捷的棕色狐狸在日落时跳过河岸附近的懒狗"
    # Ajoutez d'autres langues et phrases ici
}

# une variable globale pour indiquer que l'utilisateur doit uploader un vocal pour tester sa pronociation

audio_response_fields = {
    'audio_response_on': True,
    'audio_response_off': False,
}
prononciation_fields = {
    'prononciation_on': True,
    'prononciation_off': False,
}

lingua = 'italien'
langue_apprentissage = langues[lingua]['langue_apprentissage']
langue_nom = langues[lingua]['langue_nom']
langue_code = langues[lingua]['code_langue']
google_language_code = langues[lingua]['google_language_code']
google_voice_name = langues[lingua]['google_voice_name']

# === CONFIGURATION AZURE (deprecated)===
REFERENCE_TEXT = reference_texts.get(langue_code, "The quick brown fox jumps over the lazy dog")

# Configurer les points d'accès API
WHISPER_ENDPOINT = 'https://api.openai.com/v1/audio/transcriptions'
CHATGPT_ENDPOINT = 'https://api.openai.com/v1/completions'


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

# Fonction pour afficher une phrase colorée en fonction des scores des syllabes
def colorize_text_for_syllables(parsed_result):
    # Extraire les mots et syllabes
    text_with_colors = []
    
    for word in parsed_result['NBest'][0]['Words']:
        word_text = word['Word']
        
        # Parcours des syllabes dans chaque mot
        colored_syllables = []
        for syllable in word.get('Syllables', []):
            syllable_text = syllable['Syllable']
            syllable_score = syllable['PronunciationAssessment'].get('AccuracyScore', 0)
            
            # Déterminer la couleur en fonction du score
            if syllable_score <= 30:
                color = 'red'
            elif syllable_score <= 75:
                color = 'orange'
            else:
                color = 'green'
            
            # Ajouter la syllabe colorée
            colored_syllables.append(f'<span style="color:{color}">{syllable_text}</span>')
        
        # Ajouter les syllabes colorées au mot, séparées par des espaces
        text_with_colors.append(' '.join(colored_syllables))
    
    # Joindre tous les mots avec un espace pour la phrase complète
    return ' '.join(text_with_colors)


def set_lang(lang):
    global lingua
    lingua = lang
    global langue_apprentissage
    langue_apprentissage = langues[lang]['langue_apprentissage']
    global langue_nom
    langue_nom = langues[lang]['langue_nom']
    print(f"langue changée pour {langue_nom}")


app = Flask(__name__)



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
        print("Message marqué comme lu.")
        return True
    else:
        print(f"Erreur lors du marquage du message comme lu : {response.status_code} - {response.text}")
        return False

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


def uploader_audio_sur_facebook(ogg_buffer):
    url_upload = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/media"
    headers = {
        'Authorization': f'Bearer {WHATSAPP_API_TOKEN}'
    }
    files = {
#        'file': ('contenuaudio.mp3', BytesIO(audio_content), 'audio/mpeg')  # Utiliser BytesIO pour simuler un fichier
        'file': ('voice.ogg', ogg_buffer, 'audio/ogg')
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
        #model="gpt-5",
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


def synthesize_with_google(text, voice_name, language_code, output_filename="",
                           speaking_rate=1.0, pitch=0.0):
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        speaking_rate=float(speaking_rate),
        pitch=float(pitch)
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # Création du fichier temporaire WAV
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
        wav_file.write(response.audio_content)
        wav_path = wav_file.name

    # Fichier temporaire OGG
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as ogg_file:
        ogg_path = ogg_file.name

    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", wav_path,
            "-acodec", "libopus",
            "-ar", "48000",
            "-ac", "1",
            ogg_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Lire le fichier OGG en mémoire
        with open(ogg_path, "rb") as f:
            ogg_buffer = BytesIO(f.read())
        ogg_buffer.name = "audio.ogg"

        # Sauvegarde locale si un chemin de sortie est fourni
        if output_filename:
            os.makedirs(os.path.dirname(output_filename), exist_ok=True)
            with open(output_filename, "wb") as out_file:
                out_file.write(ogg_buffer.getvalue())
            print(f"[Google TTS] Audio enregistré dans : {output_filename}")
        else:
            print("[Google TTS] Aucun enregistrement local demandé.")

        return ogg_buffer

    finally:
        os.remove(wav_path)
        os.remove(ogg_path)


# --- Fonction de sauvegarde de la mémoire ---
# def save_memory():
#     global memory
    
#     with open(Chat_save_dir+'memory.json', 'w') as f:
#         json.dump(memory, f)
        
def save_memory():
    global memory
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob("memory.json")

    # Convertir le dictionnaire en JSON
    json_data = json.dumps(memory)
    blob.upload_from_string(json_data, content_type='application/json')
        
# def load_memory():
#     global memory
#     try:
#         with open(Chat_save_dir + 'memory.json', 'r') as f:
#             memory = json.load(f)
#             #print(memory)
#         print("Mémoire chargée avec succès.")
#     except FileNotFoundError:
#         memory = {}
#         print("Fichier memory.json introuvable, initialisation d'une mémoire vide.")
#     except json.JSONDecodeError:
#         memory = {}
#         print("Erreur de lecture du fichier JSON, initialisation d'une mémoire vide.")

def load_memory():
    global memory
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob("memory.json")

    try:
        if blob.exists():
            json_data = blob.download_as_text()
            memory = json.loads(json_data)
            print("Mémoire chargée avec succès.")
        else:
            memory = {}
            print("Fichier memory.json introuvable, initialisation d'une mémoire vide.")
    except json.JSONDecodeError:
        memory = {}
        print("Erreur de lecture du fichier JSON, initialisation d'une mémoire vide.")


def get_file_path(stamp, phone_number):
    file_path = f"{Chat_save_dir}Professore {langue_nom}-Chat with {str(phone_number)}-{stamp}.txt"
    # print (f"File path ({stamp}: {file_path}")
    # print ("coucou")
    return file_path

def read_discussion(stamp, phone_number):
    file_path = get_file_path(stamp, phone_number)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            script_content = file.read()
    else:
        return ""
    return script_content

# def add_to_context(entry,stamp, phone_number):
#     file_path = get_file_path(stamp,phone_number)
#     with open(file_path, 'a+', encoding='utf-8') as file:
#         file.write(entry)
#         file.write('\n')
#  #(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Restart server - Memory = empty"   

def add_to_context(entry,stamp, phone_number):
    file_path = get_file_path(stamp,phone_number)
    content = entry + "\n"
    append_text_to_file(file_path, content)

# def log_prononciation_html(text, phone_number):
#     # Chemin du fichier de sortie
#     output_file_path = Chat_save_dir + "Prononciation_Assessment"+phone_number+".html"
    
#     # Sauvegarde du texte colorisé dans un fichier HTML
#     with open(output_file_path, "a+", encoding="utf-8") as file:
#         file.write(text)

#     print(f"Résultat sauvegardé dans : {output_file_path}")    

#     # Afficher le texte coloré dans un format HTML
#     #print(colored_text)
def log_prononciation_html(text, phone_number):
    # Chemin du fichier de sortie
    output_file_path = Chat_save_dir + "Prononciation_Assessment"+phone_number+".html"
    
    append_text_to_file(output_file_path, text)

    print(f"Résultat prononciation sauvegardé dans : {output_file_path}")    

    # Afficher le texte coloré dans un format HTML
    #print(colored_text)

# # --- Fonction d'évaluation de prononciation ---
# def PronunciationEvaluation(REFERENCE_TEXT, language,audio_url,phone_number="###"):

#     print(f"Phrase de test : {REFERENCE_TEXT}")

#     #récupération du fichier et conversation au format attendu
#     headers_whatsapp = {
#         'Authorization': f'Bearer {WHATSAPP_API_TOKEN}'
#     }

#     response_audio = requests.get(audio_url, headers=headers_whatsapp)

#     if response_audio.status_code != 200:
#         raise Exception(f"Erreur de téléchargement du fichier audio: {response_audio.text}")

#     unique_id = str(uuid.uuid4())
#     original_filename = f"audio_temp_{unique_id}.mp3"
#     converted_filename = f"converted_{unique_id}.wav"

#     try:
#         # Sauvegarde temporaire de l'audio d'origine
#         with open(original_filename, "wb") as audio_file:
#             audio_file.write(response_audio.content)

#         # Conversion en wav (mono, 16kHz, s16)
#         ffmpeg_command = [
#             "ffmpeg", "-y", "-i", original_filename,
#             "-ar", "16000", "-ac", "1", "-sample_fmt", "s16",
#             converted_filename
#         ]
#         result = subprocess.run(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
#         if result.returncode != 0:
#             raise Exception(f"Erreur de conversion avec ffmpeg : {result.stderr.decode()}")
            



#         speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
#         audio_config = speechsdk.audio.AudioConfig(filename=converted_filename)  # Adjusted path
    
#         pron_config = speechsdk.PronunciationAssessmentConfig(
#             reference_text=REFERENCE_TEXT,
#             grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
#             # granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
#             granularity=speechsdk.PronunciationAssessmentGranularity.Word,
#             enable_miscue=True
#         )
    
#         recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
#         pron_config.apply_to(recognizer)
    
#         print("Évaluation de la prononciation en cours...")
    
#         result = recognizer.recognize_once()
#     finally:
#         print("done")
#     #     # Nettoyage des fichiers temporaires
#     #     for f in [original_filename, converted_filename]:
#     #         if os.path.exists(f):
#     #             os.remove(f)


#     if result.reason == speechsdk.ResultReason.RecognizedSpeech:
#         json_result = result.properties[speechsdk.PropertyId.SpeechServiceResponse_JsonResult]
#         parsed = json.loads(json_result)

#         # Appliquer la coloration sur la phrase
        
#         return parsed  # Renvoie le résultat JSON pour un traitement ultérieur
#     else:
#         print(f"Erreur de reconnaissance : {result.reason}")
#         return None


# --- Fonction de recontact via WhatsApp ---
def recontact_users():
    today = datetime.now()
    NB_DAYS=0 # Par exemple, recontacter après X jours d'inactivité
    restricted_list = ['33633861297']
    print("Scan la base de numéros pour recontacte")
    for phone_number, user_data in memory.items():
        if (phone_number not in restricted_list):
            continue
        last_interaction = user_data.get('last_interaction', today)
        lingua = user_data.get('lingua', "italien")
        days_since_last_interaction = (today - last_interaction).days
        print(f"days since last interaction = {days_since_last_interaction}")
        if days_since_last_interaction >= NB_DAYS:  
            catchup_message = langues[lingua]['catchup_phrase']
            envoyer_texte_whatsapp(phone_number, catchup_message)
            
            # google_voice_name = langues[lingua]['google_voice_name']
            # google_language_code = langues[lingua]['google_language_code']
            # synthesize_with_google(message, google_voice_name, google_language_code)
            # audio_file_path = os.path.join(rep, "recontact_message.mp3")
            # envoyer_audio_whatsapp(phone_number, audio_file_path)

def stop_contact(phone_number):
    memory[phone_number]['do_not_contact'] = True
    save_memory()  # Sauvegarder la mémoire après modification
    print(f"User {phone_number} opted out of contact.")



def conversation(lingua, audio_url, phone_number):
    global memory
    langue_apprentissage = langues[lingua]['langue_apprentissage']
    langue_nom = langues[lingua]['langue_nom']
    #print("Mode pronciation",memory[phone_number]['prononciationMode'])

    transcription_text = transcribe_audio_from_url(audio_url)
    print(f"Transcription de l'audio : {transcription_text}")
    add_to_context(transcription_text, "PLAIN", phone_number)
    print("ModePrononciaion: ",memory[phone_number]['prononciationMode'])
    if (memory[phone_number]['prononciationMode']):
#        EVAL_TEXT = reference_texts.get(language, "The quick brown fox jumps over the lazy dog")
        evaluation_jspon = PronunciationEvaluation(transcription_text, langue_code,audio_url, phone_number)
        PROMPT = "voici l'output json de la fonction d'analyse du langage d'azure imagine que tu es un assistant d'apprentissage de langue : je veux que tu produises en retour un tres court paragraphe (3 4 bullet points maximum, ) qui mette en avant sur les principales syllabes, phonemes ou mots qui posent problème. Donne des détails (qualitatifs plutôt que quantitatifs, l'information sur le % de précision n'est pas tres instructif) si ils sont fournis : par exemple omission, insertion, en précisant ce que cela veut dire..). Commence par une phrase courte qui donne une synthese globale de la performance, en rapport avec les chiffres de synthese de l'évaluation : "
        evaluation_assessment = f">> Evaluation de prononciation du texte *{transcription_text}*:\n"+ analyze_caption_with_chatgpt(PROMPT+str(evaluation_jspon), content="")
        print(evaluation_assessment)
        envoyer_texte_whatsapp(phone_number, evaluation_assessment)
        divider = str(datetime.now())+"<br>#####################################<br>"
        log_prononciation_html(divider + evaluation_assessment.replace('\n','<br>')+'<br>', phone_number)        
        colored_text = colorize_text_for_syllables(evaluation_jspon) +'<br><br>'
        log_prononciation_html(colored_text, phone_number)


    prompt_reformul = f"renvoie moi la version correcte en {langue_nom} de : {transcription_text} (notamment si il y a des mots qui sont dits en française, traduis-les. juste la phrase corrigée, n'ajoute rien d'autre avant et après)"
    Context = f"Voici mes précédents messages dans cette conversation : \n {read_discussion('REFORMUL', phone_number)}\n et voici une liste de sujets de conversation possibles {FichesConvers}"
    reformulation = analyze_caption_with_chatgpt(prompt_reformul)

    print(f"Phrase reformulée : {reformulation}")
    envoyer_texte_whatsapp(phone_number, f"Phrase reformulée : {reformulation}")        
    add_to_context(reformulation, "REFORMUL", phone_number)
    if (memory[phone_number]['prononciationMode']):
        audio_response = synthesize_with_google(transcription_text, google_voice_name, google_language_code,speaking_rate=0.7 )
        return "", audio_response
       
    prompt = f"Agis comme un professeur de {langue_nom}. Ton but est d'avoir une conversation avec moi : {reformulation}"
    response = analyze_caption_with_chatgpt(prompt, content=Context)
#    print("coucou test1")

    add_to_context(reformulation, "REFORMUL", phone_number)
#    print("coucou test2")

    print(f"Réponse du professeur de {langue_nom} : {response}")
    if memory[phone_number]['create_audio_response']:
#        print("coucouaudioresponde")
        
        # def synthesize_with_google(text, filename, voice_name, language_code, speaking_rate=1.0, pitch=0.0):

        audio_response = synthesize_with_google(response, google_voice_name, google_language_code)
        return response, audio_response
    else:
        return response, None

def catch_escape_word(text, escape_symbol="."):
    if (text == ""):
        return ""
    elif (text[0] == escape_symbol):
        keyword = text.split()[0][1:]
        return keyword
    
log_msg_id_file = Chat_save_dir + "log_msg_id_ChatBot.txt"
# Lecture des message_id existants dans le fichier log
try :
    with open(log_msg_id_file, 'r') as file:
        Messages_id = [line.split()[1] for line in file]
except Exception as e:
    print (f"fichier {log_msg_id_file} non trouvé, Messages_id =[]")   

def log_debug_summary(source_label, data):
    print(f"\n===== [{source_label}] Webhook reçu =====")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"User-Agent: {request.headers.get('User-Agent')}")
    print(f"IP: {request.remote_addr}")

    # Synthèse structurée
    try:
        value = data['entry'][0]['changes'][0]['value']
        msg_list = value.get('messages')
        statuses = value.get('statuses')
        if msg_list:
            msg = msg_list[0]
            msg_type = msg.get('type', 'unknown')
            msg_id = msg.get('id', 'no_id')
            print(f"Type de message : {msg_type}")
            print(f"ID du message : {msg_id}")

            if msg_type == 'text':
                text = msg.get('text', {}).get('body', '')
                print(f"Contenu (texte) : {text[:50]}...")

            elif msg_type == 'button':
                payload = msg.get('button', {}).get('payload', '')
                print(f"Payload (bouton) : {payload[:50]}...")

            elif msg_type == 'interactive':
                inter = msg.get('interactive', {})
                payload = inter.get('button_reply', {}).get('id') or inter.get('list_reply', {}).get('id')
                print(f"Payload (interactive) : {payload[:50] if payload else 'None'}")

            elif msg_type == 'image':
                media_id = msg.get('image', {}).get('id', '')
                caption = msg.get('image', {}).get('caption', '')
                print(f"Image ID: {media_id}")
                print(f"Légende : {caption[:50]}...")

            else:
                print(f"Type de message non traité : {msg_type}")

        elif statuses:
            print("Événement de statut reçu")
        else:
            print("Aucun message ou statut trouvé dans 'value'.")

    except Exception as e:
        print(f"Erreur dans le résumé structuré : {e}")
        print(f"Payload brut tronqué : {str(data)[:300]}...")     

# --- Server webwook ---
@app.route('/')
def home():
    return "Bienvenue sur l'appli WhatsApp"

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print(f"Requête reçue : mode={mode}, token={token}, challenge={challenge}")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200  # TEXTE BRUT attendu par Meta
    else:
        return "Forbidden", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    global memory
    try:
        data = request.get_json()
 #       log_debug_summary("HELLO", data)

        if not data or not isinstance(data, dict) or 'entry' not in data:
            print(f"Webhook ignoré : bruit ou ping - data = {data}")
            return "Événement ignoré (bruit)", 200

        changes = data['entry'][0].get('changes', [])
        if not changes:
            print("Pas de 'changes' dans le message, probablement un bruit")
            return "Événement ignoré (pas de changement)", 200

        value = changes[0].get('value', {})
        
        # Statuts (accusés de réception par ex.)
        if 'statuses' in value:
            print("Statut reçu, non traité")
            return "Statut ignoré", 200

        # Aucun message réel
        if 'messages' not in value:
            print("Pas de messages présents, bruit")
            return "Aucun message à traiter", 200

 
        try:
            phone_number = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
            print(f"Numéro de téléphone: {phone_number}")
        except Exception as a:
            print(f"Exception {a} : payload was {data}")
            return "Erreur dans les données du message", 400
        try:
            message_id = data['entry'][0]['changes'][0]['value']['messages'][0]['id']
            print(f"Id du message: {message_id}")
            try:
                flag = mark_as_read(message_id)
                if flag == False: return "Message ignoré (mauvais adressage ?)", 200
            except Exception as e:
                error_msg = str(e)
                print(f"Erreur lors du marquage du message comme lu : {error_msg}")
        except Exception as g:
            print(f"Exception {g} : unable to read message's id")
            return "Message ignoré (IP illisble)", 200




            
        try:
            timestamp_str = data['entry'][0]['changes'][0]['value']['messages'][0]["timestamp"]  # e.g., "1712607227"
            timestamp_int = int(timestamp_str)
            message_datetime = datetime.fromtimestamp(timestamp_int)
            now = datetime.utcnow()
            
            print("time_stamp du message :", message_datetime)
        
            # Si le message a plus de 1 heure, on l'ignore
            if now - message_datetime > timedelta(hours=1):
                print(f"Message {message_id} trop ancien, ignoré.")
                return "Événement ignoré", 200
        except Exception as g:
            print(f"Exception {g} : unable to compare message's timestamp")
       
        try:
            if message_id in Messages_id:
                print(f"Message {message_id} déjà reçu, >> ignoré")
                return "Message déjà reçu", 200
            else:
                # with open(log_msg_id_file, 'a') as file:
                #     timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                #     file.write(f"{timestamp} {message_id}\n")
                Messages_id.append(message_id)
        except Exception as g:
            print(f"Exception {g} : unable to read message's id")
            
        try:
            if(MaintenanceMode and not(phone_number in MaintenanceAutorized)):
                msg = "🚧Service en maintenance - Merci de revenir plus tard !🚧"
                print(msg)
                envoyer_texte_whatsapp(phone_number, msg)
                return "Site en maintenance", 200
        except Exception as g:
            print(f"Exception {g} : unable to read message's id")                
                
                
        try:
            message = data['entry'][0]['changes'][0]['value']['messages'][0]


            if phone_number not in memory:
                memory[phone_number] = {
                    'lingua': 'italien',
                    'create_audio_response': False,
                    'last_interaction': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # Initialisation de la date de dernière interaction
                    'do_not_contact':False,
                    'prononciationMode' : False
                }
                envoyer_texte_whatsapp(phone_number, "tapez '.help' pour connaitre le fonctionnement")

            # Extraction des variables spécifiques à l'utilisateur
            lingua = memory[phone_number]['lingua']
            
# --- escape words ---

            if message.get('type') == 'text':
                message_text = message['text']['body']
                escape_word = catch_escape_word(message_text, '.')
                print(f"Escape word : {escape_word} ")

                if escape_word in langues:
                    response = f"Escape value captée : {escape_word}, changement de langue pour {langues[escape_word]['langue_apprentissage']}"
                    l = langues[escape_word]['langue_nom']
                    memory[phone_number]['lingua'] = l
                    save_memory()
                    envoyer_texte_whatsapp(phone_number, response)
                    set_lang(l)
                elif escape_word in audio_response_fields:
                    memory[phone_number]['create_audio_response']= audio_response_fields[escape_word]
                    save_memory()
                    msg="change setting: 'create_audio_response' =" + str(memory[phone_number]['create_audio_response'])
                    print(msg)
                    envoyer_texte_whatsapp(phone_number, msg)
                elif escape_word in prononciation_fields:
                    memory[phone_number]['prononciationMode']= prononciation_fields[escape_word]
                    msg = "change setting: 'prononciationMode' =" + str(memory[phone_number]['prononciationMode'])
                    print(msg)
                    envoyer_texte_whatsapp(phone_number, msg)
                    save_memory()
                elif escape_word == "prononciation":
                    print("Évaluation de prononciation demandée.")
                    PrononciationTestPhrase = reference_texts.get(langue_code, "The quick brown fox jumps over the lazy dog")
                    msg = f"*Exercice de Prononciation* : Merci d'uploader un vocal en lisant cette phrase :\n {PrononciationTestPhrase}"
                    envoyer_texte_whatsapp(phone_number, msg)
                    memory[phone_number]['prononciationMode'] = True                 
                elif escape_word == "stop":
                    stop_contact(phone_number)
                    save_memory()
                    envoyer_texte_whatsapp(phone_number, "Vous ne recevrez plus de messages.")
                elif escape_word == "help":
                    print ("escape word: help")
                    envoyer_texte_whatsapp(phone_number, help_text)
                elif escape_word == "story":
                    print("Escape word : '.story'")
                    PROMPT_Story = f"tu es un professeur de {langue_apprentissage} et je suis ton élève. Sur la base de nos conversations ci-dessous et mon niveau, écris-moi une histoire en environ 200 mots, que je vais essayer de comprendre. Nous pourrons en parler ensuite.\n{read_discussion('REFORMUL', phone_number)}"
                    resp = analyze_caption_with_chatgpt(PROMPT_Story)
                    envoyer_texte_whatsapp(phone_number, resp)
                else:
                    msg = "Commande non reconnue, essayer .help"
                    print(msg)
                    envoyer_texte_whatsapp(phone_number, msg)

            audio_url = None
            if message.get('type') == 'audio':
                try:
                    audio_id = message['audio']['id']
                    audio_url = get_audio_url(audio_id)
                except KeyError as e:
                    print(f"KeyError : {e}")
                    return "Clé audio absente", 400

        except Exception as e:
            print(f"Exception : {e}")
            audio_url = None

        if audio_url is not None:
            reponse, audio_response = conversation(lingua, audio_url, phone_number)
            envoyer_texte_whatsapp(phone_number, reponse)
            if audio_response is not None:
                 
                envoyer_audio_whatsapp(phone_number, audio_response)

        save_memory()  # Sauvegarder la mémoire à chaque interaction
        return jsonify({"status": "message envoyé"}), 200
    
        recontact_users()

    except Exception as e:
        print("Erreur lors du traitement des données :")
        print(f"Type : {type(e).__name__}")
        print(f"Message : {e}")
        print("Traceback :")
        traceback.print_exc()
        return "Erreur interne", 500

if __name__ == '__main__':
    print("Re(start) Professore conversation")
    print ("Maintenance mode: ", MaintenanceMode)
    load_memory()
#    print(memory)
    recontact_users()
    app.run(host='0.0.0.0', port=8080)









