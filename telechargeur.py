"""
Contient toute la logique de téléchargement avec yt-dlp.
Gère :
- L'organisation automatique des dossiers (playlist vs vidéo simple)
- L'intégration des métadonnées et miniatures dans les fichiers audio
- La correction des numéros de piste après téléchargement
"""

import os
import re
import yt_dlp
import shutil
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from mutagen import File as MutagenFile

# ---------------------------------------------------------
# Utilitaires généraux
# ---------------------------------------------------------

def nettoyer_url_video_simple(url):
    """
    Supprime les paramètres 'list' et 'index' d'une URL YouTube.
    Utile quand l'utilisateur ajoute une "vidéo simple" mais colle
    un lien copié depuis une playlist (ex: https://youtu.be/XXX?list=YYY).
    """
    morceaux = urlparse(url)
    parametres = parse_qs(morceaux.query)

    # On retire les paramètres liés à la playlist
    parametres.pop('list', None)
    parametres.pop('index', None)

    nouvelle_query = urlencode(parametres, doseq=True)

    url_nettoyee = urlunparse((
        morceaux.scheme,
        morceaux.netloc,
        morceaux.path,
        morceaux.params,
        nouvelle_query,
        morceaux.fragment
    ))

    # Si l'URL nettoyée finit par un "?" vide, on l'enlève
    url_nettoyee = url_nettoyee.rstrip('?')

    return url_nettoyee


def hook_progression(d):
    """Affiche la progression du téléchargement en cours."""
    if d['status'] == 'downloading':
        pourcentage = d.get('_percent_str', 'N/A')
        vitesse = d.get('_speed_str', 'N/A')
        print(f"\r⬇️  {pourcentage} - Vitesse : {vitesse}", end='')

    elif d['status'] == 'finished':
        print(f"\n✅ Téléchargement terminé, conversion en cours...")


def ecrire_log(chemin_log, message):
    """Ajoute une ligne au fichier de log, si un chemin est défini."""
    if chemin_log:
        with open(chemin_log, 'a', encoding='utf-8') as f:
            f.write(message + '\n')


def nettoyer_nom_dossier(nom):
    """
    Nettoie une chaîne pour qu'elle soit utilisable comme nom de dossier.
    Enlève les caractères interdits sur Windows/Mac/Linux.
    """
    nom_nettoye = re.sub(r'[\\/*?:"<>|]', "", nom)
    return nom_nettoye.strip()


def est_une_playlist(url):
    """
    Détermine si une URL correspond à une playlist ou une vidéo simple.
    On regarde simplement si 'list=' est présent dans l'URL.
    """
    return "list=" in url

# ---------------------------------------------------------
# Gestion des playlists et dossiers
# ---------------------------------------------------------

def obtenir_nom_playlist(url):
    """
    Récupère le titre de la playlist SANS télécharger les vidéos.
    Utilise extract_flat='in_playlist' pour rester rapide.
    """
    options_info = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(options_info) as ydl:
            info = ydl.extract_info(url, download=False)
            titre = info.get('title')

            if not titre or titre == 'NA':
                print("⚠️  Nom de playlist introuvable, utilisation d'un nom générique.")
                titre = f"Playlist_{info.get('id', 'inconnue')}"

            return nettoyer_nom_dossier(titre)

    except Exception as e:
        print(f"⚠️  Impossible de récupérer le nom de la playlist : {e}")
        return "Playlist_Inconnue"


def verifier_ffmpeg(afficher_message=True):
    """
    Vérifie que ffmpeg est installé et accessible.
    afficher_message=False permet de l'utiliser silencieusement.
    """
    chemin_ffmpeg = shutil.which("ffmpeg")

    if chemin_ffmpeg is None:
        if afficher_message:
            print("❌ ERREUR : ffmpeg n'est pas installé ou pas dans le PATH.")
            print("   Télécharge-le ici : https://ffmpeg.org/download.html")
        return False

    return True

# ---------------------------------------------------------
# Construction des options yt-dlp
# ---------------------------------------------------------

def construire_options(config, dossier_sortie, nom_playlist=None, est_playlist=False):
    """
    Construit les options pour yt-dlp.
    est_playlist : indique si c'est une playlist ou une vidéo simple.
    """

    if not os.path.exists(dossier_sortie):
        os.makedirs(dossier_sortie)
        print(f"📁 Dossier créé : {dossier_sortie}")

    postprocessors = [
        {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': config['format'],
            'preferredquality': config['qualite'],
        },
        {
            'key': 'FFmpegMetadata',
            'add_metadata': True,
        },
        {
            'key': 'EmbedThumbnail',
        },
    ]

    options = {
        'format': 'bestaudio/best',
        'postprocessors': postprocessors,
        'writethumbnail': True,
        'outtmpl': os.path.join(dossier_sortie, config['nom_fichier']),
        'progress_hooks': [hook_progression],
        'ignoreerrors': True,
        'quiet': config['silencieux'],
        'no_warnings': config['silencieux'],
        'retries': config['retries'],
        'fragment_retries': config['retries'],
        'noplaylist': not est_playlist,
    }

    # --- Métadonnées personnalisées ---
    regles = [
        # Artiste = nom de la chaîne YouTube (uploader)
        '%(uploader)s:(?P<meta_artist>.+)',
    ]

    if est_playlist:
        # Numéro de piste = position dans la playlist
        regles.append('%(playlist_index)s:(?P<meta_track>.+)')

    options['parse_metadata'] = regles

    return options


def verifier_resultat_telechargement(dossier, format_attendu):
    """
    Vérifie après coup qu'il n'y a pas de fichiers dans un format
    inattendu (webm, m4a...) qui indiqueraient un échec de conversion.
    """
    fichiers_suspects = []

    for fichier in os.listdir(dossier):
        chemin = os.path.join(dossier, fichier)
        if os.path.isfile(chemin):
            extension = fichier.split('.')[-1].lower()
            if extension != format_attendu and extension not in ('jpg', 'png', 'webp'):
                fichiers_suspects.append(fichier)

    if fichiers_suspects:
        print(f"\n⚠️  ATTENTION : {len(fichiers_suspects)} fichier(s) n'ont PAS")
        print(f"   été convertis en .{format_attendu} :")
        for f in fichiers_suspects:
            print(f"   - {f}")
        print("   → Vérifie que ffmpeg fonctionne correctement.\n")

    return len(fichiers_suspects) == 0

# ---------------------------------------------------------
# Correction des métadonnées après téléchargement
# ---------------------------------------------------------

def corriger_numeros_de_piste(dossier, format_audio):
    """
    Parcourt les fichiers d'un dossier de playlist et force le tag
    'tracknumber' à correspondre au préfixe numérique du nom de fichier
    (ex: "03 - Titre.mp3" → tracknumber = "3").
    """
    if not os.path.isdir(dossier):
        return

    for fichier in os.listdir(dossier):
        if not fichier.lower().endswith(f".{format_audio}"):
            continue

        chemin = os.path.join(dossier, fichier)

        # On extrait le numéro en début de nom (ex: "03 - Titre.mp3" → "03")
        match = re.match(r'^(\d+)', fichier)
        if not match:
            continue

        numero = str(int(match.group(1)))

        try:
            audio = MutagenFile(chemin, easy=True)
            if audio is None:
                continue
            if audio.tags is None:
                audio.add_tags()

            audio["tracknumber"] = numero
            audio.save()
        except Exception as e:
            print(f"⚠️  Impossible de corriger le n° de piste pour {fichier} : {e}")

# ---------------------------------------------------------
# Téléchargement
# ---------------------------------------------------------

def telecharger_une_tache(tache, dossier_de_base, config, retourner_fichiers=False):
    """
    Télécharge une seule tâche (playlist ou vidéo simple).
    tache : dictionnaire avec 'url', 'dossier', 'type'
    """

    fichiers_avant = set()
    if retourner_fichiers and os.path.exists(dossier_de_base):
        for racine, _, fichiers in os.walk(dossier_de_base):
            for f in fichiers:
                fichiers_avant.add(os.path.join(racine, f))

    if not verifier_ffmpeg():
        return (False, []) if retourner_fichiers else False

    url = tache['url']
    est_playlist = (tache.get('type') == 'playlist')

    nom_playlist = None

    if est_playlist:
        nom_playlist = obtenir_nom_playlist(url)
        dossier_final = os.path.join(dossier_de_base, nom_playlist)
        print(f"📀 Playlist : '{nom_playlist}'")
    else:
        dossier_final = dossier_de_base
        print("🎵 Vidéo simple (playlist ignorée si présente dans l'URL).")

    options = construire_options(
        config,
        dossier_final,
        nom_playlist=nom_playlist,
        est_playlist=est_playlist
    )

    print("\n" + "=" * 50)
    print(f"🔗 URL      : {url}")
    print(f"📁 Dossier  : {dossier_final}")
    print("=" * 50 + "\n")

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        verifier_resultat_telechargement(dossier_final, config['format'])

        if est_playlist:
            print("\n🔧 Correction des numéros de piste...")
            corriger_numeros_de_piste(dossier_final, config['format'])

        if retourner_fichiers:
            fichiers_apres = set()
            if os.path.exists(dossier_de_base):
                for racine, _, fichiers in os.walk(dossier_de_base):
                    for f in fichiers:
                        fichiers_apres.add(os.path.join(racine, f))
            nouveaux_fichiers = list(fichiers_apres - fichiers_avant)
            return True, nouveaux_fichiers

        print(f"\n🎉 Terminé pour : {dossier_final}")
        return True

    except yt_dlp.utils.DownloadError as e:
        message = f"❌ Erreur de téléchargement pour {url} : {e}"
        print(f"\n{message}")
        ecrire_log(config.get('log'), message)
        return False

    except Exception as e:
        message = f"❌ Erreur inattendue pour {url} : {e}"
        print(f"\n{message}")
        ecrire_log(config.get('log'), message)
        return False


def telecharger_toutes_les_taches(config):
    """
    Parcourt toutes les tâches définies dans la config
    et les télécharge une par une.
    """
    taches = config.get('taches', [])

    if not taches:
        print("⚠️  Aucune tâche à télécharger. Ajoute une playlist ou une vidéo depuis le menu.")
        return

    print(f"\n📋 {len(taches)} tâche(s) à traiter.\n")

    dossier_de_base = config.get('dossier_sortie_defaut', 'downloads')

    resultats = []

    for i, tache in enumerate(taches, start=1):
        print(f"\n--- Tâche {i}/{len(taches)} ---")

        # Si un dossier spécifique est défini pour cette tâche
        dossier_tache = tache.get('dossier', '')
        if dossier_tache and dossier_tache != dossier_de_base:
            dossier_cible = os.path.join(dossier_de_base, dossier_tache)
        else:
            dossier_cible = dossier_de_base

        succes = telecharger_une_tache(tache, dossier_cible, config)

        resultats.append({
            "url": tache['url'],
            "succes": succes
        })

    # --- Résumé final ---
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DU TÉLÉCHARGEMENT")
    print("=" * 50)

    nb_succes = sum(1 for r in resultats if r['succes'])
    nb_echecs = len(resultats) - nb_succes

    print(f"✅ Réussites : {nb_succes}")
    print(f"❌ Échecs    : {nb_echecs}")

    if nb_echecs > 0:
        print("\nURLs en échec :")
        for r in resultats:
            if not r['succes']:
                print(f"   - {r['url']}")