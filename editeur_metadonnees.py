"""
Éditeur de métadonnées pour les fichiers audio téléchargés.
Permet de corriger titre / artiste / album / année / genre, fichier par fichier
ou en masse sur un dossier entier, ainsi que de renommer
le fichier (1 par 1 uniquement) selon des formats prédéfinis
ou un nom totalement libre.
Gestion aussi de l'artwork (pochette).
"""
import os
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error as ID3Error
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover

EXTENSIONS_AUDIO = (".mp3", ".m4a", ".flac", ".wav", ".opus", ".ogg")

FORMATS_PREDEFINIS = {
    "1": {
        "nom": "[Position]-[Titre]",
        "gabarit": lambda titre, artiste, album, piste, ext: (
            f"{piste.zfill(2) if piste else '00'} - {titre}{ext}"
        ),
    },
    "2": {
        "nom": "[Artiste]-[Titre]",
        "gabarit": lambda titre, artiste, album, piste, ext: (
            f"{artiste or 'Inconnu'} - {titre}{ext}"
        ),
    },
    "3": {
        "nom": "[Titre]",
        "gabarit": lambda titre, artiste, album, piste, ext: (
            f"{titre}{ext}"
        ),
    },
    "4": {
        "nom": "[Position]-[Titre]-[Artiste]",
        "gabarit": lambda titre, artiste, album, piste, ext: (
            f"{piste.zfill(2) if piste else '00'} - {titre} - {artiste or 'Inconnu'}{ext}"
        ),
    },
}

# ---------------------------------------------------------
# Utilitaires d'affichage
# ---------------------------------------------------------

def effacer_ecran():
    """Efface la console (fonctionne sur Windows, Mac et Linux)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def pause():
    """Attend que l'utilisateur appuie sur Entrée."""
    input("\nAppuie sur Entrée pour continuer...")


def afficher_titre(titre):
    """Affiche un titre encadré."""
    print("=" * 50)
    print(f"  {titre}")
    print("=" * 50)

# ---------------------------------------------------------
# Lecture et écriture des tags
# ---------------------------------------------------------

def lire_tags(chemin_fichier):
    """
    Retourne un dict {titre, artiste, album, piste, annee, genre} lu depuis le fichier.
    Renvoie None si le fichier n'a pas pu être lu.
    """
    try:
        audio = MutagenFile(chemin_fichier, easy=True)
        if audio is None:
            return None

        def get(cle):
            valeur = audio.get(cle)
            return valeur[0] if valeur else ""

        return {
            "titre": get("title"),
            "artiste": get("artist"),
            "album": get("album"),
            "piste": get("tracknumber"),
            "annee": get("date"),
            "genre": get("genre"),
        }
    except Exception as e:
        print(f"⚠️  Impossible de lire {chemin_fichier} : {e}")
        return None


def ecrire_tags(chemin_fichier, titre=None, artiste=None, album=None, piste=None, annee=None, genre=None):
    """
    Écrit les tags fournis (les None ne sont pas modifiés).
    Retourne True si succès, False sinon.
    """
    try:
        audio = MutagenFile(chemin_fichier, easy=True)
        if audio is None:
            return False

        # Certains formats (wav...) n'ont pas de tags par défaut
        if audio.tags is None:
            audio.add_tags()

        if titre is not None:
            if titre == "":
                if "title" in audio:
                    del audio["title"]
            else:
                audio["title"] = titre

        if artiste is not None:
            if artiste == "":
                if "artist" in audio:
                    del audio["artist"]
            else:
                audio["artist"] = artiste

        if album is not None:
            if album == "":
                if "album" in audio:
                    del audio["album"]
            else:
                audio["album"] = album

        if piste is not None:
            if piste == "":
                if "tracknumber" in audio:
                    del audio["tracknumber"]
            else:
                audio["tracknumber"] = piste

        if annee is not None:
            if annee == "":
                if "date" in audio:
                    del audio["date"]
            else:
                audio["date"] = annee

        if genre is not None:
            if genre == "":
                if "genre" in audio:
                    del audio["genre"]
            else:
                audio["genre"] = genre

        audio.save()
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'écriture des tags sur {chemin_fichier} : {e}")
        return False

# ---------------------------------------------------------
# Gestion de l'artwork (pochette)
# ---------------------------------------------------------

def lire_artwork_presente(chemin_fichier):
    """
    Vérifie si le fichier contient déjà une image de pochette.
    Retourne True/False.
    """
    ext = os.path.splitext(chemin_fichier)[1].lower()

    try:
        if ext == ".mp3":
            audio = MP3(chemin_fichier, ID3=ID3)
            if audio.tags is None:
                return False
            for tag in audio.tags.values():
                if tag.FrameID == "APIC":
                    return True
            return False

        elif ext == ".flac":
            audio = FLAC(chemin_fichier)
            return len(audio.pictures) > 0

        elif ext == ".m4a":
            audio = MP4(chemin_fichier)
            return "covr" in audio.tags if audio.tags else False

        else:
            return False

    except Exception:
        return False


def appliquer_artwork(chemin_fichier, chemin_image):
    """
    Applique une image (jpg/png) comme pochette du fichier audio.
    Gère mp3 (ID3/APIC), flac (Picture) et m4a (MP4Cover).
    Retourne True si succès, False sinon.
    """
    ext = os.path.splitext(chemin_fichier)[1].lower()
    ext_image = os.path.splitext(chemin_image)[1].lower()

    if ext_image not in (".jpg", ".jpeg", ".png"):
        print(f"❌ Format d'image non supporté : {ext_image} (utilise .jpg ou .png)")
        return False

    mime = "image/jpeg" if ext_image in (".jpg", ".jpeg") else "image/png"

    try:
        with open(chemin_image, "rb") as f:
            donnees_image = f.read()

        if ext == ".mp3":
            try:
                audio = ID3(chemin_fichier)
            except ID3Error:
                audio = ID3()

            # On retire les anciennes pochettes avant d'ajouter la nouvelle
            audio.delall("APIC")

            audio.add(APIC(
                encoding=3,
                mime=mime,
                type=3,  # 3 = "cover front"
                desc="Cover",
                data=donnees_image,
            ))
            audio.save(chemin_fichier, v2_version=3)
            return True

        elif ext == ".flac":
            audio = FLAC(chemin_fichier)
            audio.clear_pictures()

            image = Picture()
            image.type = 3
            image.mime = mime
            image.desc = "Cover"
            image.data = donnees_image

            audio.add_picture(image)
            audio.save()
            return True

        elif ext == ".m4a":
            audio = MP4(chemin_fichier)
            if audio.tags is None:
                audio.add_tags()

            format_cover = MP4Cover.FORMAT_JPEG if ext_image in (".jpg", ".jpeg") else MP4Cover.FORMAT_PNG
            audio.tags["covr"] = [MP4Cover(donnees_image, imageformat=format_cover)]
            audio.save()
            return True

        else:
            print(f"❌ Format de fichier non supporté pour l'artwork : {ext}")
            return False

    except Exception as e:
        print(f"❌ Erreur lors de l'application de l'artwork sur {os.path.basename(chemin_fichier)} : {e}")
        return False


def demander_chemin_image():
    """
    Demande à l'utilisateur le chemin d'une image et vérifie qu'il existe.
    Retourne le chemin ou None si annulé/invalide.
    """
    chemin = input("👉 Chemin complet de l'image (.jpg / .png) : ").strip().strip('"')

    if not chemin:
        return None

    if not os.path.isfile(chemin):
        print(f"❌ Fichier introuvable : {chemin}")
        return None

    ext = os.path.splitext(chemin)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        print(f"❌ Format non supporté : {ext} (utilise .jpg ou .png)")
        return None

    return chemin

# ---------------------------------------------------------
# Recherche des fichiers dans downloads/
# ---------------------------------------------------------

def lister_fichiers_audio(dossier_downloads):
    """Liste tous les fichiers audio du dossier et ses sous-dossiers."""
    resultats = []

    if not os.path.isdir(dossier_downloads):
        return resultats

    for racine, dirs, fichiers in os.walk(dossier_downloads):
        for f in fichiers:
            if f.lower().endswith(EXTENSIONS_AUDIO):
                chemin_complet = os.path.join(racine, f)
                affichage = os.path.relpath(chemin_complet, dossier_downloads)
                resultats.append((chemin_complet, affichage))

    return sorted(resultats, key=lambda x: x[1].lower())


def lister_sous_dossiers(dossier_downloads):
    """Liste tous les sous-dossiers du dossier de téléchargement."""
    if not os.path.isdir(dossier_downloads):
        return []

    return sorted([
        d for d in os.listdir(dossier_downloads)
        if os.path.isdir(os.path.join(dossier_downloads, d))
    ])

# ---------------------------------------------------------
# Renommage de fichier
# ---------------------------------------------------------

def nettoyer_pour_nom_fichier(texte):
    """Nettoie une chaîne pour qu'elle soit valide comme nom de fichier."""
    interdits = '<>:"/\\|?*'
    for c in interdits:
        texte = texte.replace(c, "")
    return texte.strip()

def nettoyer_titre(titre, mots_a_retirer, sensible_casse=False):
    """
    Retire les mots-clés indiqués du titre, puis nettoie
    les espaces/tirets/parenthèses résiduels.
    """
    resultat = titre

    for mot in mots_a_retirer:
        if not mot:
            continue
        if sensible_casse:
            resultat = resultat.replace(mot, "")
        else:
            # Remplacement insensible à la casse
            import re
            resultat = re.sub(re.escape(mot), "", resultat, flags=re.IGNORECASE)

    # Nettoyage des restes typiques : " - ", "--", parenthèses/crochets vides, espaces multiples
    import re
    resultat = re.sub(r"\(\s*\)", "", resultat)       # ( )
    resultat = re.sub(r"\[\s*\]", "", resultat)       # [ ]
    resultat = re.sub(r"^\s*-+\s*", "", resultat)     # tiret en début
    resultat = re.sub(r"\s*-+\s*$", "", resultat)     # tiret en fin
    resultat = re.sub(r"\s{2,}", " ", resultat)       # espaces multiples
    resultat = resultat.strip(" -_")

    return resultat.strip()


def menu_nettoyer_titres(fichiers):
    """
    Menu pour retirer des mots-clés communs des titres d'un dossier.
    Retourne un dict {chemin_fichier: nouveau_titre} ou None si annulé.
    """
    effacer_ecran()
    afficher_titre("NETTOYER LES TITRES")

    # On lit tous les titres actuels pour donner un aperçu
    titres_actuels = {}
    for chemin_fichier in fichiers:
        tags = lire_tags(chemin_fichier)
        if tags:
            titres_actuels[chemin_fichier] = tags.get("titre") or os.path.splitext(os.path.basename(chemin_fichier))[0]

    if not titres_actuels:
        print("❌ Aucun titre lisible dans ce dossier.")
        pause()
        return None

    print("📋 Titres actuels :\n")
    for titre in titres_actuels.values():
        print(f"  • {titre}")

    print("\n💡 Entre un ou plusieurs mots/expressions à retirer de TOUS les titres.")
    print("   Exemples : \"AMENRA - \", \"(Official Music Video)\", \"[Official Audio]\"")
    print("   Sépare plusieurs expressions par un ' ; ' (point-virgule).")
    print("   Laisse vide pour annuler.\n")

    saisie = input("👉 Mot(s)/expression(s) à retirer : ").strip()

    if not saisie:
        return None

    mots_a_retirer = [m.strip() for m in saisie.split(";") if m.strip()]

    if not mots_a_retirer:
        print("\n❌ Rien à retirer, annulation.")
        pause()
        return None

    sensible = input("Sensible à la casse ? (oui/non, défaut non) : ").strip().lower() == "oui"

    # Calcul de l'aperçu avant/après
    nouveaux_titres = {}
    for chemin_fichier, titre_actuel in titres_actuels.items():
        nouveau_titre = nettoyer_titre(titre_actuel, mots_a_retirer, sensible)
        nouveaux_titres[chemin_fichier] = nouveau_titre

    effacer_ecran()
    afficher_titre("APERÇU DU NETTOYAGE DES TITRES")

    for chemin_fichier, titre_actuel in titres_actuels.items():
        nouveau = nouveaux_titres[chemin_fichier]
        if nouveau != titre_actuel:
            print(f"  \"{titre_actuel}\"  →  \"{nouveau}\"")
        else:
            print(f"  \"{titre_actuel}\"  (inchangé)")

    confirmation = input(f"\n⚠️  Appliquer ce nettoyage sur {len(nouveaux_titres)} titre(s) ? (oui/non) : ").strip().lower()

    if confirmation != "oui":
        print("\n❌ Annulé.")
        pause()
        return None

    return nouveaux_titres

def renommer_fichier(chemin_fichier, nouveau_nom_sans_ext):
    """
    Renomme un fichier. Demande confirmation si un fichier
    avec ce nom existe déjà. Retourne le nouveau chemin ou None.
    """
    dossier = os.path.dirname(chemin_fichier)
    ext = os.path.splitext(chemin_fichier)[1]

    nouveau_nom = nettoyer_pour_nom_fichier(nouveau_nom_sans_ext) + ext
    nouveau_chemin = os.path.join(dossier, nouveau_nom)

    if os.path.exists(nouveau_chemin) and nouveau_chemin != chemin_fichier:
        print(f"⚠️  Un fichier nommé '{nouveau_nom}' existe déjà dans ce dossier.")
        confirmation = input("Écraser ? (oui/non) : ").strip().lower()
        if confirmation != "oui":
            return None

    try:
        os.rename(chemin_fichier, nouveau_chemin)
        return nouveau_chemin
    except Exception as e:
        print(f"❌ Erreur lors du renommage : {e}")
        return None


def menu_renommer_fichier(chemin_fichier, tags_actuels):
    """Menu pour renommer un fichier selon un format prédéfini ou libre."""
    effacer_ecran()
    afficher_titre("RENOMMER LE FICHIER")

    titre = tags_actuels.get("titre") or "Sans_titre"
    artiste = tags_actuels.get("artiste") or ""
    album = tags_actuels.get("album") or ""
    piste = tags_actuels.get("piste") or ""
    ext = os.path.splitext(chemin_fichier)[1]

    print(f"Fichier actuel : {os.path.basename(chemin_fichier)}\n")
    print("Choisis un format de nom de fichier :\n")
    for cle, info in FORMATS_PREDEFINIS.items():
        exemple = info["gabarit"](titre, artiste, album, piste, ext)
        print(f"{cle}. {info['nom']}  →  exemple : {exemple}")
    print("5. Nom totalement libre")
    print("0. Ne pas renommer / annuler")

    choix = input("\n👉 Ton choix : ").strip()

    if choix in FORMATS_PREDEFINIS:
        gabarit = FORMATS_PREDEFINIS[choix]["gabarit"]
        nom_genere = gabarit(titre, artiste, album, piste, ext)
        nom_sans_ext = os.path.splitext(nom_genere)[0]

        nouveau_chemin = renommer_fichier(chemin_fichier, nom_sans_ext)
        if nouveau_chemin:
            print(f"\n✅ Fichier renommé en : {os.path.basename(nouveau_chemin)}")
            return nouveau_chemin
        else:
            print("\n❌ Renommage annulé ou échoué.")
            return chemin_fichier

    elif choix == "5":
        nom_libre = input("\n👉 Nouveau nom (sans extension) : ").strip()
        if not nom_libre:
            print("\n❌ Nom vide, annulation.")
            return chemin_fichier

        nouveau_chemin = renommer_fichier(chemin_fichier, nom_libre)
        if nouveau_chemin:
            print(f"\n✅ Fichier renommé en : {os.path.basename(nouveau_chemin)}")
            return nouveau_chemin
        else:
            print("\n❌ Renommage annulé ou échoué.")
            return chemin_fichier

    else:
        return chemin_fichier

# ---------------------------------------------------------
# Modification 1 par 1
# ---------------------------------------------------------

def menu_modifier_un_fichier(config):
    """Menu pour modifier les métadonnées d'un fichier (1 par 1)."""
    dossier_downloads = config.get("dossier_sortie_defaut", "downloads")

    effacer_ecran()
    afficher_titre("MODIFIER UN FICHIER")

    fichiers = lister_fichiers_audio(dossier_downloads)

    if not fichiers:
        print("Aucun fichier audio trouvé dans le dossier de téléchargement.")
        pause()
        return

    for i, (chemin_complet, affichage) in enumerate(fichiers):
        print(f"[{i}] {affichage}")

    choix = input("\n👉 Numéro du fichier à modifier (Entrée pour annuler) : ").strip()

    if not choix:
        return

    try:
        index = int(choix)
        chemin_fichier, affichage = fichiers[index]
    except (ValueError, IndexError):
        print("\n❌ Numéro invalide.")
        pause()
        return

    tags = lire_tags(chemin_fichier)

    if tags is None:
        print("\n❌ Impossible de lire les métadonnées de ce fichier.")
        pause()
        return

    while True:
        effacer_ecran()
        afficher_titre(f"MODIFIER : {affichage}")

        a_une_pochette = lire_artwork_presente(chemin_fichier)
        statut_pochette = "✅ Présente" if a_une_pochette else "❌ Absente"

        print(f"1. Titre    : {tags['titre']}")
        print(f"2. Artiste  : {tags['artiste']}")
        print(f"3. Album    : {tags['album']}")
        print(f"4. Piste n° : {tags['piste']}")
        print(f"5. Année    : {tags['annee']}")
        print(f"6. Genre    : {tags['genre']}")
        print(f"7. Pochette : {statut_pochette}")
        print(f"8. Renommer le fichier")
        print(f"9. ⬅️  Retour (sauvegarde déjà appliquée à chaque modif)")

        sous_choix = input("\n👉 Choix : ").strip()

        if sous_choix == "1":
            valeur = input(f"Nouveau titre (Entrée pour garder '{tags['titre']}') : ").strip()
            if valeur:
                if ecrire_tags(chemin_fichier, titre=valeur):
                    tags["titre"] = valeur
                    print("✅ Titre modifié.")
                pause()

        elif sous_choix == "2":
            valeur = input(f"Nouvel artiste (Entrée pour garder '{tags['artiste']}') : ").strip()
            if valeur:
                if ecrire_tags(chemin_fichier, artiste=valeur):
                    tags["artiste"] = valeur
                    print("✅ Artiste modifié.")
                pause()

        elif sous_choix == "3":
            valeur = input(f"Nouvel album (Entrée pour garder '{tags['album']}') : ").strip()
            if valeur:
                if ecrire_tags(chemin_fichier, album=valeur):
                    tags["album"] = valeur
                    print("✅ Album modifié.")
                pause()

        elif sous_choix == "4":
            valeur = input(f"Nouveau numéro de piste (Entrée pour garder '{tags['piste']}') : ").strip()
            if valeur:
                if ecrire_tags(chemin_fichier, piste=valeur):
                    tags["piste"] = valeur
                    print("✅ Numéro de piste modifié.")
                pause()

        elif sous_choix == "5":
            valeur = input(f"Nouvelle année (Entrée pour garder '{tags['annee']}') : ").strip()
            if valeur:
                if ecrire_tags(chemin_fichier, annee=valeur):
                    tags["annee"] = valeur
                    print("✅ Année modifiée.")
                pause()

        elif sous_choix == "6":
            valeur = input(f"Nouveau genre (Entrée pour garder '{tags['genre']}') : ").strip()
            if valeur:
                if ecrire_tags(chemin_fichier, genre=valeur):
                    tags["genre"] = valeur
                    print("✅ Genre modifié.")
                pause()

        elif sous_choix == "7":
            print(f"\nPochette actuelle : {statut_pochette}")
            chemin_image = demander_chemin_image()
            if chemin_image:
                if appliquer_artwork(chemin_fichier, chemin_image):
                    print("✅ Pochette mise à jour.")
                else:
                    print("❌ Échec de la mise à jour de la pochette.")
                pause()

        elif sous_choix == "8":
            nouveau_chemin = menu_renommer_fichier(chemin_fichier, tags)
            if nouveau_chemin != chemin_fichier:
                chemin_fichier = nouveau_chemin
                affichage = os.path.relpath(chemin_fichier, dossier_downloads)
            pause()

        elif sous_choix == "9":
            return

        else:
            print("\n❌ Choix invalide.")
            pause()

# ---------------------------------------------------------
# Modification en masse (dossier entier)
# ---------------------------------------------------------

def menu_modifier_un_dossier(config):
    """Menu pour modifier les métadonnées de tous les fichiers d'un dossier."""
    dossier_downloads = config.get("dossier_sortie_defaut", "downloads")

    effacer_ecran()
    afficher_titre("MODIFIER UN DOSSIER ENTIER")

    sous_dossiers = lister_sous_dossiers(dossier_downloads)

    print("[R] Utiliser downloads/ directement (fichiers à la racine)")
    for i, d in enumerate(sous_dossiers):
        print(f"[{i}] {d}")

    choix = input("\n👉 Dossier à traiter (Entrée pour annuler) : ").strip()

    if not choix:
        return

    if choix.upper() == "R":
        chemin_dossier = dossier_downloads
        nom_affichage = "downloads/"
    else:
        try:
            index = int(choix)
            nom_dossier = sous_dossiers[index]
            chemin_dossier = os.path.join(dossier_downloads, nom_dossier)
            nom_affichage = nom_dossier
        except (ValueError, IndexError):
            print("\n❌ Choix invalide.")
            pause()
            return

    fichiers = [
        os.path.join(chemin_dossier, f)
        for f in os.listdir(chemin_dossier)
        if f.lower().endswith(EXTENSIONS_AUDIO)
    ]

    if not fichiers:
        print("\n❌ Aucun fichier audio dans ce dossier.")
        pause()
        return

    # --- État des modifications à appliquer ---
    renommer = False
    gabarit = None
    nom_format_choisi = ""

    modifier_artiste = False
    nouvel_artiste = ""

    modifier_album = False
    nouvel_album = ""

    modifier_annee = False
    nouvelle_annee = ""

    modifier_genre = False
    nouveau_genre = ""

    modifier_pochette = False
    chemin_image_pochette = ""

    nettoyer_titres_actif = False
    nouveaux_titres = {}

    # --- Menu de sélection des actions ---
    while True:
        effacer_ecran()
        afficher_titre(f"MODIFIER LE DOSSIER : {nom_affichage}")
        print(f"📁 {len(fichiers)} fichier(s) trouvé(s).\n")

        print(f"1. Renommer les fichiers          [{'✅ ' + nom_format_choisi if renommer else '❌ Non'}]")
        print(f"2. Modifier l'artiste             [{'✅ ' + nouvel_artiste if modifier_artiste else '❌ Non'}]")
        print(f"3. Modifier l'album               [{'✅ ' + nouvel_album if modifier_album else '❌ Non'}]")
        print(f"4. Modifier l'année               [{'✅ ' + nouvelle_annee if modifier_annee else '❌ Non'}]")
        print(f"5. Modifier le genre              [{'✅ ' + nouveau_genre if modifier_genre else '❌ Non'}]")
        print(f"6. Modifier la pochette           [{'✅ ' + os.path.basename(chemin_image_pochette) if modifier_pochette else '❌ Non'}]")
        print(f"7. Nettoyer les titres            [{'✅ Oui (' + str(len(nouveaux_titres)) + ' titre(s))' if nettoyer_titres_actif else '❌ Non'}]")
        print("8. ✅ Valider et appliquer")
        print("9. ⬅️  Annuler et retour")

        choix_action = input("\n👉 Choix : ").strip()

        if choix_action == "1":
            print("\nChoisis le format de renommage :\n")
            for cle, info in FORMATS_PREDEFINIS.items():
                print(f"{cle}. {info['nom']}")
            print("0. Annuler le renommage")

            choix_format = input("\n👉 Ton choix : ").strip()

            if choix_format in FORMATS_PREDEFINIS:
                gabarit = FORMATS_PREDEFINIS[choix_format]["gabarit"]
                nom_format_choisi = FORMATS_PREDEFINIS[choix_format]["nom"]
                renommer = True
            else:
                renommer = False
                gabarit = None
                nom_format_choisi = ""

        elif choix_action == "2":
            valeur = input("\nNouvel artiste (Entrée pour annuler) : ").strip()
            if valeur:
                nouvel_artiste = valeur
                modifier_artiste = True
            else:
                modifier_artiste = False
                nouvel_artiste = ""

        elif choix_action == "3":
            valeur = input("\nNouvel album (Entrée pour annuler) : ").strip()
            if valeur:
                nouvel_album = valeur
                modifier_album = True
            else:
                modifier_album = False
                nouvel_album = ""

        elif choix_action == "4":
            valeur = input("\nNouvelle année (Entrée pour annuler) : ").strip()
            if valeur:
                nouvelle_annee = valeur
                modifier_annee = True
            else:
                modifier_annee = False
                nouvelle_annee = ""

        elif choix_action == "5":
            valeur = input("\nNouveau genre (Entrée pour annuler) : ").strip()
            if valeur:
                nouveau_genre = valeur
                modifier_genre = True
            else:
                modifier_genre = False
                nouveau_genre = ""

        elif choix_action == "6":
            print("\n🖼️  Applique une même pochette à tous les fichiers du dossier.")
            chemin_image = demander_chemin_image()
            if chemin_image:
                chemin_image_pochette = chemin_image
                modifier_pochette = True
            else:
                modifier_pochette = False
                chemin_image_pochette = ""

        elif choix_action == "7":
            resultat = menu_nettoyer_titres(fichiers)
            if resultat:
                nouveaux_titres = resultat
                nettoyer_titres_actif = True
            else:
                nettoyer_titres_actif = False
                nouveaux_titres = {}

        elif choix_action == "8":
            if not renommer and not modifier_artiste and not modifier_album and not modifier_annee and not modifier_genre and not modifier_pochette and not nettoyer_titres_actif:
                print("\n❌ Aucune modification sélectionnée.")
                pause()
                continue
            break

        elif choix_action == "9":
            return

        else:
            print("\n❌ Choix invalide.")
            pause()

    # --- Aperçu des modifications ---
    apercu = []
    for chemin_fichier in fichiers:
        tags = lire_tags(chemin_fichier)
        ext = os.path.splitext(chemin_fichier)[1]
        titre = tags.get("titre") or os.path.splitext(os.path.basename(chemin_fichier))[0]

        if nettoyer_titres_actif and chemin_fichier in nouveaux_titres:
            titre = nouveaux_titres[chemin_fichier]

        if tags is None:
            apercu.append((chemin_fichier, None, "⚠️  Tags illisibles, ignoré"))
            continue

        nouveau_nom = None
        if renommer:
            titre = tags.get("titre") or os.path.splitext(os.path.basename(chemin_fichier))[0]
            artiste_pour_nom = nouvel_artiste if modifier_artiste else (tags.get("artiste") or "")
            album_pour_nom = nouvel_album if modifier_album else (tags.get("album") or "")
            piste = tags.get("piste") or ""
            if nettoyer_titres_actif:
                print(f"\n🧹 Nettoyage des titres appliqué sur {len(nouveaux_titres)} fichier(s)")
            nouveau_nom = gabarit(titre, artiste_pour_nom, album_pour_nom, piste, ext)

        apercu.append((chemin_fichier, nouveau_nom, None))

    effacer_ecran()
    afficher_titre("APERÇU DES MODIFICATIONS")

    for chemin_fichier, nouveau_nom, erreur in apercu:
        ancien_nom = os.path.basename(chemin_fichier)
        if erreur:
            print(f"{ancien_nom}  →  {erreur}")
        elif nouveau_nom:
            print(f"{ancien_nom}  →  {nouveau_nom}")
        else:
            print(f"{ancien_nom}  (métadonnées seulement)")

    if modifier_artiste:
        print(f"\n🎤 Artiste → \"{nouvel_artiste}\" pour tous les fichiers")
    if modifier_album:
        print(f"💿 Album → \"{nouvel_album}\" pour tous les fichiers")
    if modifier_annee:
        print(f"📅 Année → \"{nouvelle_annee}\" pour tous les fichiers")
    if modifier_genre:
        print(f"🎸 Genre → \"{nouveau_genre}\" pour tous les fichiers")
    if modifier_pochette:
        print(f"🖼️  Pochette → \"{os.path.basename(chemin_image_pochette)}\" pour tous les fichiers")

    confirmation = input(f"\n⚠️  Confirmer les modifications sur {len(fichiers)} fichier(s) ? (oui/non) : ").strip().lower()

    if confirmation != "oui":
        print("\n❌ Annulé.")
        pause()
        return

    reussites = 0
    echecs = 0
    ignores = 0

    for chemin_fichier, nouveau_nom, erreur in apercu:
        if erreur:
            ignores += 1
            continue

        chemin_actuel = chemin_fichier

        if nettoyer_titres_actif and chemin_actuel in nouveaux_titres:
            succes_titre = ecrire_tags(chemin_actuel, titre=nouveaux_titres[chemin_actuel])
            if not succes_titre:
                echecs += 1
                continue

        if modifier_artiste or modifier_album or modifier_annee or modifier_genre:
            succes_tags = ecrire_tags(
                chemin_actuel,
                artiste=nouvel_artiste if modifier_artiste else None,
                album=nouvel_album if modifier_album else None,
                annee=nouvelle_annee if modifier_annee else None,
                genre=nouveau_genre if modifier_genre else None,
            )
            if not succes_tags:
                echecs += 1
                continue

        if modifier_pochette:
            succes_pochette = appliquer_artwork(chemin_actuel, chemin_image_pochette)
            if not succes_pochette:
                echecs += 1
                continue

        if renommer and nouveau_nom:
            nom_sans_ext = os.path.splitext(nouveau_nom)[0]
            nouveau_chemin = renommer_fichier(chemin_actuel, nom_sans_ext)
            if not nouveau_chemin:
                echecs += 1
                continue

        reussites += 1

    print(f"\n✅ {reussites} fichier(s) modifié(s) avec succès.")
    if echecs:
        print(f"❌ {echecs} fichier(s) en échec.")
    if ignores:
        print(f"⚠️  {ignores} fichier(s) ignoré(s) (tags illisibles).")

    pause()

# ---------------------------------------------------------
# Menu principal de l'éditeur
# ---------------------------------------------------------

def menu_editeur_metadonnees(config):
    """Menu principal de l'éditeur de métadonnées."""
    while True:
        effacer_ecran()
        afficher_titre("ÉDITEUR DE MÉTADONNÉES")
        print("""
1. Modifier un fichier (1 par 1) — titre / artiste / album / année / genre / pochette / renommage
2. Modifier un dossier entier (en masse) — renommage et/ou artiste / album / année / genre / pochette
3. ⬅️  Retour au menu principal
""")
        choix = input("👉 Choix : ").strip()

        if choix == "1":
            menu_modifier_un_fichier(config)

        elif choix == "2":
            menu_modifier_un_dossier(config)

        elif choix == "3":
            return

        else:
            print("\n❌ Choix invalide.")
            pause()