"""
Menu interactif affiché quand on lance le programme
en double-cliquant dessus (mode "classique").
"""
import os
import subprocess
import tempfile
import json
import time
import sys
from config import (
    charger_config, sauvegarder_config,
    ajouter_tache, supprimer_tache, vider_taches
)
from telechargeur import telecharger_toutes_les_taches, nettoyer_url_video_simple
from editeur_metadonnees import menu_editeur_metadonnees
from progression import lire_progression, nettoyer_progression, FICHIER_PROGRESSION

def effacer_ecran():
    """Efface la console (fonctionne sur Windows, Mac et Linux)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def pause():
    """Attend que l'utilisateur appuie sur Entrée avant de continuer."""
    input("\nAppuie sur Entrée pour continuer...")


def afficher_titre(titre):
    """Affiche un titre encadré, pour que ce soit lisible."""
    print("=" * 50)
    print(f"  {titre}")
    print("=" * 50)


def menu_principal():
    """Affiche le menu principal et retourne le choix de l'utilisateur."""
    effacer_ecran()
    afficher_titre("TÉLÉCHARGEUR AUDIO YOUTUBE")
    print("""
1. 📋 Voir la liste des téléchargements (tâches)
2. ➕ Ajouter une playlist à la liste
3. ➕ Ajouter une vidéo simple à la liste
4. ➖ Supprimer une tâche de la liste
5. 🗑️  Vider toute la liste
6. ⬇️  Lancer tous les téléchargements
7. ⚙️  Modifier les paramètres (format, qualité...)
8. 🏷️  Modifier les métadonnées des fichiers téléchargés
9. ❌ Quitter
""")
    return input("👉 Choix : ").strip()


def afficher_taches(config):
    """Affiche la liste des tâches enregistrées."""
    effacer_ecran()
    afficher_titre("LISTE DES TÉLÉCHARGEMENTS")

    taches = config.get("taches", [])

    if not taches:
        print("Aucune tâche pour le moment.")
    else:
        for i, t in enumerate(taches):
            emoji = "🎵" if t["type"] == "video" else "📀"
            print(f"[{i}] {emoji} {t['type'].upper()} → {t['dossier']}")
            print(f"     {t['url']}")

    pause()


def ajouter_playlist(config):
    """
    Demande une URL de playlist. Le dossier sera automatiquement
    'downloads/Nom_De_La_Playlist' sauf si l'utilisateur en précise un.
    """
    effacer_ecran()
    afficher_titre("AJOUTER UNE PLAYLIST")

    url = input("👉 URL de la playlist YouTube : ").strip()
    if not url:
        print("❌ URL vide, annulation.")
        pause()
        return

    print(f"\nℹ️  Par défaut, un sous-dossier sera créé automatiquement")
    print(f"   dans '{config['dossier_sortie_defaut']}' avec le nom de la playlist.")

    dossier = input(
        "👉 Dossier personnalisé (Entrée pour utiliser le nom automatique) : "
    ).strip()

    if not dossier:
        dossier = config['dossier_sortie_defaut']

    ajouter_tache(config, url, dossier, type_contenu="playlist")
    print(f"\n✅ Playlist ajoutée.")
    pause()


def ajouter_video(config):
    """Ajoute une vidéo simple à la liste des tâches."""
    effacer_ecran()
    afficher_titre("AJOUTER UNE VIDÉO SIMPLE")

    url = input("\n🔗 Colle l'URL de la vidéo : ").strip()

    if not url:
        print("❌ URL vide, annulation.")
        pause()
        return

    # On nettoie l'URL pour enlever tout paramètre playlist
    url_originale = url
    url = nettoyer_url_video_simple(url)

    if url != url_originale:
        print(f"\nℹ️  L'URL contenait des paramètres de playlist, elle a été nettoyée :")
        print(f"   Avant : {url_originale}")
        print(f"   Après : {url}")

    dossier = input(
        f"\n📁 Nom du sous-dossier (Entrée pour '{config['dossier_sortie_defaut']}') : "
    ).strip()

    if not dossier:
        dossier = config['dossier_sortie_defaut']

    ajouter_tache(config, url, dossier, type_contenu="video")

    print("\n✅ Vidéo ajoutée avec succès !")
    pause()


def menu_supprimer_tache(config):
    """Permet de supprimer une tâche précise de la liste."""
    effacer_ecran()
    afficher_titre("SUPPRIMER UNE TÂCHE")

    taches = config.get("taches", [])

    if not taches:
        print("Aucune tâche à supprimer.")
        pause()
        return

    for i, t in enumerate(taches):
        print(f"[{i}] {t['type'].upper()} → {t['dossier']} ({t['url']})")

    choix = input("\n👉 Index de la tâche à supprimer (Entrée pour annuler) : ").strip()

    if not choix:
        return

    try:
        index = int(choix)
        supprimee = supprimer_tache(config, index)
        if supprimee:
            print(f"\n✅ Tâche supprimée : {supprimee['url']}")
        else:
            print("\n❌ Index invalide.")
    except ValueError:
        print("\n❌ Merci d'entrer un nombre valide.")

    pause()


def menu_vider_taches(config):
    """Demande confirmation puis vide toute la liste."""
    effacer_ecran()
    afficher_titre("VIDER LA LISTE")

    confirmation = input(
        "⚠️  Es-tu sûr de vouloir tout supprimer ? (oui/non) : "
    ).strip().lower()

    if confirmation == "oui":
        vider_taches(config)
        print("\n✅ Liste vidée.")
    else:
        print("\n❌ Annulé.")

    pause()


def menu_parametres(config):
    """
    Menu permettant de modifier les paramètres globaux
    (format, qualité, dossier par défaut, etc.)
    """
    while True:
        effacer_ecran()
        afficher_titre("PARAMÈTRES")
        print(f"""
1. Dossier de sortie par défaut : {config['dossier_sortie_defaut']}
2. Format audio                 : {config['format']}
3. Qualité (kbps)                : {config['qualite']}
4. Nombre de tentatives (retries): {config['retries']}
5. Nom de fichier (template)     : {config['nom_fichier']}
6. Mode silencieux               : {config['silencieux']}
7. Fichier de log                : {config['log'] or '(aucun)'}
8. ⬅️  Retour au menu principal
""")
        choix = input("👉 Choix : ").strip()

        if choix == "1":
            valeur = input("Nouveau dossier par défaut : ").strip()
            if valeur:
                config['dossier_sortie_defaut'] = valeur
                sauvegarder_config(config)

        elif choix == "2":
            print("Formats disponibles : mp3, wav, m4a, flac, opus, vorbis")
            valeur = input("Nouveau format : ").strip().lower()
            if valeur in ["mp3", "wav", "m4a", "flac", "opus", "vorbis"]:
                config['format'] = valeur
                sauvegarder_config(config)
            else:
                print("❌ Format invalide.")
                pause()

        elif choix == "3":
            print("Qualités disponibles : 128, 192, 256, 320")
            valeur = input("Nouvelle qualité : ").strip()
            if valeur in ["128", "192", "256", "320"]:
                config['qualite'] = valeur
                sauvegarder_config(config)
            else:
                print("❌ Qualité invalide.")
                pause()

        elif choix == "4":
            valeur = input("Nombre de tentatives : ").strip()
            if valeur.isdigit():
                config['retries'] = int(valeur)
                sauvegarder_config(config)
            else:
                print("❌ Merci d'entrer un nombre.")
                pause()

        elif choix == "5":
            print("Variables disponibles : %(title)s, %(playlist_index)s, %(ext)s, %(uploader)s...")
            valeur = input("Nouveau template : ").strip()
            if valeur:
                config['nom_fichier'] = valeur
                sauvegarder_config(config)

        elif choix == "6":
            config['silencieux'] = not config['silencieux']
            sauvegarder_config(config)

        elif choix == "7":
            valeur = input("Chemin du fichier de log (vide pour désactiver) : ").strip()
            config['log'] = valeur
            sauvegarder_config(config)

        elif choix == "8":
            return

        else:
            print("❌ Choix invalide.")
            pause()


def lancer_menu():
    config = charger_config()

    while True:
        effacer_ecran()
        afficher_titre("TÉLÉCHARGEUR AUDIO YOUTUBE")

        progression = lire_progression()
        if progression and not progression["termine"]:
            print("🔄 Un téléchargement est en cours en arrière-plan !\n")

        print("1. 📋 Voir la liste des téléchargements (tâches)")
        print("2. ➕ Ajouter une playlist à la liste")
        print("3. ➕ Ajouter une vidéo simple à la liste")
        print("4. ➖ Supprimer une tâche de la liste")
        print("5. 🗑️  Vider toute la liste")
        print("6. ⬇️  Lancer tous les téléchargements (fenêtre séparée)")
        print("7. ⚙️  Modifier les paramètres (format, qualité...)")
        print("8. 🏷️  Modifier les métadonnées des fichiers téléchargés")
        print("9. 📊 Voir l'état du téléchargement en cours")
        print("10. ❌ Quitter")

        choix = input("\n👉 Choix : ").strip()

        if choix == "1":
            afficher_taches(config)
        elif choix == "2":
            ajouter_playlist(config)
        elif choix == "3":
            ajouter_video(config)
        elif choix == "4":
            menu_supprimer_tache(config)
        elif choix == "5":
            menu_vider_taches(config)
        elif choix == "6":
            lancer_telechargements_en_fenetre_separee(config)
            pause()
        elif choix == "7":
            menu_parametres(config)
        elif choix == "8":
            menu_editeur_metadonnees(config)
        elif choix == "9":
            afficher_etat_telechargement_en_cours()
        elif choix == "10":
            print("\n👋 Au revoir !")
            break
        else:
            print("\n❌ Choix invalide.")
            pause()


def lancer_telechargements_en_fenetre_separee(config):
    """
    Lance les téléchargements dans une nouvelle fenêtre de terminal,
    et permet à l'utilisateur d'éditer les métadonnées pendant ce temps.
    """
    taches = config.get("taches", [])
    if not taches:
        print("\n❌ Aucune tâche à télécharger.")
        pause()
        return

    nettoyer_progression()

    fichier_taches = os.path.join(tempfile.gettempdir(), "taches_dl.json")
    fichier_config = os.path.join(tempfile.gettempdir(), "config_dl.json")

    with open(fichier_taches, "w", encoding="utf-8") as f:
        json.dump(taches, f, ensure_ascii=False, indent=2)
    with open(fichier_config, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telechargement_process.py")

    if sys.platform == "win32":
        subprocess.Popen(
            ["cmd", "/c", "start", "cmd", "/c",   # ⬅️ /c au lieu de /k
             sys.executable, script_path, fichier_taches, fichier_config],
            shell=True
        )
    else:
        subprocess.Popen(
            ["x-terminal-emulator", "-e",
             f"{sys.executable} {script_path} {fichier_taches} {fichier_config}"]
        )

    print("\n✅ Téléchargement lancé dans une nouvelle fenêtre !")
    print("💡 Tu peux continuer à utiliser ce menu pour éditer les métadonnées")
    print("   des fichiers déjà téléchargés pendant que ça continue en arrière-plan.\n")

    time.sleep(2)

def afficher_etat_telechargement_en_cours():
    """Affiche l'état actuel du téléchargement en arrière-plan, si actif."""
    progression = lire_progression()

    if progression is None:
        print("\nℹ️  Aucun téléchargement en cours actuellement.")
        pause()
        return

    if progression["termine"]:
        print("\n✅ Le dernier téléchargement lancé est terminé.")
    else:
        total = progression["total_taches"]
        actuel = progression["tache_actuelle"]
        nom = progression["nom_tache_actuelle"]
        nb_fichiers = len(progression["fichiers_termines"])

        pourcentage = (actuel / total * 100) if total > 0 else 0
        largeur = 40
        remplissage = int(largeur * actuel / total) if total > 0 else 0
        barre = "█" * remplissage + "░" * (largeur - remplissage)

        print(f"\n[{barre}] {actuel}/{total} ({pourcentage:.1f}%)")
        print(f"🔗 En cours : {nom}")
        print(f"📁 Fichiers déjà téléchargés : {nb_fichiers}")

    pause()

