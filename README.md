# 🎵 Téléchargeur Audio YouTube

Un logiciel en Python permettant de télécharger des vidéos ou playlists YouTube au format audio (MP3, M4A, etc.), avec gestion complète des métadonnées (titre, artiste, album, année, genre, pochette) et renommage automatique des fichiers.

---

## 📑 Sommaire

1.  [Installation](#️-installation)
2.  [Lancement du programme](#️-lancement-du-programme)
3.  [Menu principal](#-menu-principal)
4.  [Ajouter des telechargements](#-ajouter-des-telechargements)
5.  [Lancer les telechargements](#️-lancer-les-telechargements)
6.  [Paramètres](#️-parametres)
7.  [editeur de metadonnees](#️-editeur-de-metadonnees)
8.  [Structure des dossiers](#-structure-des-dossiers)
9.  [Mise à jour de yt-dlp](#-mise-à-jour-de-yt-dlp)

---

## ⚙️ Installation

-   telecharger le zip depuit : 
-   décompresser le zip
-   Ouvre PowerShell dans le dossier du programme, puis :
    >>  python -m venv venv
    >>  venv\Scripts\activate
    >>  pip install -r requirements.txt

## ▶️ Lancement du programme

### 1️⃣ via le bureau

    lancer : launch.bat

### 2️⃣ via le terminal

dans le terminal:
    >>  venv\Scripts\activate
    >>  python main.py

## 🧭 Menu principal

    1. 📋 Voir la liste des téléchargements (tâches)
    2. ➕ Ajouter une playlist à la liste
    3. ➕ Ajouter une vidéo simple à la liste
    4. ➖ Supprimer une tâche de la liste
    5. 🗑️  Vider toute la liste
    6. ⬇️  Lancer tous les téléchargements
    7. ⚙️  Modifier les paramètres (format, qualité...)
    8. 🏷️  Modifier les métadonnées des fichiers téléchargés
    9. ❌ Quitter

    Tape le numéro correspondant à l'action désirée, puis valide avec Entrée

## ➕ Ajouter des telechargements

    Ajouter une playlist (option 2)

    -   Colle l'URL complète de la playlist YouTube (ex: https://www.youtube.com/playlist?  list=...).
    -   Le programme te propose un dossier de sortie par défaut (nom de la playlist), que tu peux personnaliser.
    -   Tous les fichiers de cette playlist seront placés dans downloads/<nom_playlist>/.

    Ajouter une vidéo simple (option 3)

    -   Colle l'URL d'une vidéo (ex: https://youtu.be/xxxxxxx ou https://www.youtube.com/watch?v=xxxxxxx).
    -   ⚠️ Si l'URL contient un paramètre de playlist (?list=...), seule la vidéo sera téléchargée, la playlist sera ignorée.
    -   Par défaut, les vidéos simples sont placées directement dans downloads/.

    Voir / Supprimer / Vider la liste (options 1, 4, 5)

    -   Ces options te permettent de consulter les tâches en attente, d'en retirer une précise, ou de tout effacer avant de lancer le téléchargement.

## ⬇️ Lancer les telechargements

    Option 6 du menu principal : lance le téléchargement de toutes les tâches actuellement dans la liste, dans l'ordre où elles ont été ajoutées.

    Pour chaque tâche, le programme affiche :

    -   L'URL traitée
    -   Le dossier de destination
    -   La progression du téléchargement
    -   Un résumé final (réussites ✅ / échecs ❌)

    Les métadonnées (titre, artiste, album, position dans l'album/playlist) sont automatiquement extraites et écrites dans chaque fichier audio téléchargé.

## ⚙️ Parametres

Option 7 du menu principal te permet de configurer :

Paramètre                               |   Description
                                        |
Format audio                            |   mp3, m4a, opus, flac, etc.
                                        |
Qualité audio                           |   bitrate (ex: 192 kbps, 320 kbps...)
                                        |
Dossier de téléchargement par défaut    |   où sont stockés les fichiers (par défaut downloads/)

Les paramètres sont sauvegardés dans un fichier config.json à la racine du projet, et sont conservés entre chaque lancement du programme.

## 🏷️ editeur de metadonnees

Option 8 du menu principal. Permet de corriger/modifier les informations des fichiers déjà téléchargés (présents dans downloads/ ou ses sous-dossiers).

Deux modes disponibles :

### 1️⃣ Modifier un fichier (1 par 1)

-   Sélectionne un fichier précis.
-   Modifie individuellement : titre, artiste, album, année, genre, pochette.
-   Possibilité de renommer le fichier selon un format prédéfini ou libre :
    -   [N°]-[Titre].[format]
    -   [Artiste]-[Titre].[format]
    -   [Titre].[format]
    -   [N°]-[Titre]-[Artiste].[format]
    -   Ou un nom totalement personnalisé

### 2️⃣ Modifier un dossier entier (en masse)

-   Sélectionne un dossier (ex: downloads/sous_dos/).
-   Choisis une ou plusieurs modifications à appliquer à tous les fichiers du dossier :

    1. Renommer les fichiers
    2. Modifier l'artiste
    3. Modifier l'album
    4. Modifier l'année
    5. Modifier le genre
    6. Modifier la pochette
    7. Nettoyer les titres (retirer un texte commun)
    8. ✅ Valider et appliquer
    9. ⬅️  Annuler et retour

-   Tu peux cocher/configurer plusieurs options en même temps avant de valider.
-   Un aperçu avant/après est toujours affiché avant l'application définitive, avec demande de confirmation.

### 🧹 Nettoyer les titres — cas d'usage
Utile quand une chaîne YouTube autre que l'artiste original met son nom dans le titre de la vidéo.
Exemple :
    ARTISTE - Titre 1   →   Titre 1
    ARTISTE - Titre 2   →   Titre 2

Tu peux retirer un ou plusieurs mots/expressions à la fois (séparés par ;) :
    👉 Mot(s)/expression(s) à retirer : ARTISTE - ; (Official Music Video) ; [Official Audio]

Le nettoyage supprime aussi automatiquement les tirets, espaces ou parenthèses vides laissés par la suppression.

## 📂 Structure des dossiers

    downloaderyt/
    ├── main.py                 # Point d'entrée du programme
    ├── menu.py                 # Gestion des menus et interface
    ├── telechargeur.py         # Logique de téléchargement (yt-dlp)
    ├── metadonnees.py          # Lecture/écriture des tags audio
    ├── config.json             # Paramètres sauvegardés (créé automatiquement)
    ├── requirements.txt        # Dépendances Python
    └── downloads/               # Dossier de sortie par défaut
        ├── video_simple.mp3
        └── Nom_de_la_Playlist/
            ├── 01-Titre1.mp3
            ├── 02-Titre2.mp3
            └── ...

## 🔄 Mise à jour de yt-dlp

YouTube modifie régulièrement ses systèmes de protection, ce qui peut casser le téléchargement
(Requested format is not available, nsig extraction failed, etc.).

Solution : mettre à jour yt-dlp régulièrement.
Avec le venv activé :
    >>  pip install -U yt-dlp

💡 Si le problème persiste après la mise à jour, vérifie aussi que FFmpeg est bien installé et à jour.

# 📜 Licence / Usage

Ce programme est destiné à un usage personnel et privé. Merci de respecter les conditions d'utilisation de YouTube et les droits d'auteur des contenus téléchargés.
