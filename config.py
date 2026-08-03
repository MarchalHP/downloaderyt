"""
Gestion du fichier de configuration JSON.
Ce module centralise la lecture/écriture des paramètres
pour que l'utilisateur n'ait pas à tout retaper à chaque lancement.
"""

import json
import os

# Nom du fichier de config (dans le même dossier que le programme)
FICHIER_CONFIG = "config.json"

# Configuration par défaut si aucun fichier n'existe encore
CONFIG_DEFAUT = {
    "dossier_sortie_defaut": "downloads",
    "format": "mp3",
    "qualite": "192",
    "retries": 3,
    "nom_fichier": "%(playlist_index)02d - %(title)s.%(ext)s",
    "silencieux": False,
    "log": "",
    # Liste des tâches : chaque tâche = une URL (playlist ou vidéo) + son dossier
    "taches": []
}


def charger_config():
    """
    Charge la configuration depuis le fichier JSON.
    Si le fichier n'existe pas, crée une config par défaut.
    """
    if not os.path.exists(FICHIER_CONFIG):
        sauvegarder_config(CONFIG_DEFAUT)
        return CONFIG_DEFAUT.copy()

    try:
        with open(FICHIER_CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # On s'assure que toutes les clés par défaut existent
        # (utile si on ajoute de nouveaux paramètres plus tard)
        for cle, valeur in CONFIG_DEFAUT.items():
            if cle not in config:
                config[cle] = valeur

        return config

    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️  Erreur de lecture du fichier config : {e}")
        print("⚠️  Utilisation de la configuration par défaut.")
        return CONFIG_DEFAUT.copy()


def sauvegarder_config(config):
    """
    Sauvegarde la configuration actuelle dans le fichier JSON.
    indent=4 rend le fichier lisible pour un humain.
    """
    try:
        with open(FICHIER_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"❌ Impossible d'enregistrer la config : {e}")


def ajouter_tache(config, url, dossier, type_contenu="playlist"):
    """
    Ajoute une nouvelle tâche (URL + dossier de sortie) à la liste.
    type_contenu : "playlist" ou "video"
    """
    tache = {
        "url": url,
        "dossier": dossier,
        "type": type_contenu
    }
    config["taches"].append(tache)
    sauvegarder_config(config)


def supprimer_tache(config, index):
    """Supprime une tâche de la liste par son index."""
    if 0 <= index < len(config["taches"]):
        tache_supprimee = config["taches"].pop(index)
        sauvegarder_config(config)
        return tache_supprimee
    return None


def vider_taches(config):
    """Supprime toutes les tâches de la liste."""
    config["taches"] = []
    sauvegarder_config(config)