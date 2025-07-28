# Image de base légère Python
FROM python:3.9-slim

# Définir le dossier de travail
WORKDIR /app

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copier les fichiers dans le conteneur
COPY . .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port attendu par Cloud Run
EXPOSE 8080

# Démarrer l'application
CMD ["python", "prof.py"]
