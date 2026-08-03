"""
Gestion de la progression du téléchargement partagée entre processus.
"""
import json
import os

FICHIER_PROGRESSION = "progression.json"


def initialiser_progression(total_taches):
    """Crée/réinitialise le fichier de progression."""
    data = {
        "total_taches": total_taches,
        "tache_actuelle": 0,
        "nom_tache_actuelle": "",
        "fichiers_termines": [],  # liste des chemins de fichiers déjà téléchargés
        "termine": False
    }
    with open(FICHIER_PROGRESSION, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def mettre_a_jour_progression(tache_actuelle=None, nom_tache=None,
                                nouveau_fichier=None, termine=None):
    """Met à jour le fichier de progression (appelé par le processus de téléchargement)."""
    if not os.path.exists(FICHIER_PROGRESSION):
        return

    with open(FICHIER_PROGRESSION, "r", encoding="utf-8") as f:
        data = json.load(f)

    if tache_actuelle is not None:
        data["tache_actuelle"] = tache_actuelle
    if nom_tache is not None:
        data["nom_tache_actuelle"] = nom_tache
    if nouveau_fichier is not None:
        data["fichiers_termines"].append(nouveau_fichier)
    if termine is not None:
        data["termine"] = termine

    with open(FICHIER_PROGRESSION, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def lire_progression():
    """Lit l'état actuel de la progression (appelé par le terminal principal)."""
    if not os.path.exists(FICHIER_PROGRESSION):
        return None
    try:
        with open(FICHIER_PROGRESSION, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def nettoyer_progression():
    """Supprime le fichier de progression une fois terminé."""
    if os.path.exists(FICHIER_PROGRESSION):
        os.remove(FICHIER_PROGRESSION)