"""
Point d'entrée du programme.
- Si lancé sans argument (double-clic) → ouvre le menu interactif
- Si lancé avec des arguments en ligne de commande → mode direct (optionnel)
"""

import sys
from menu import lancer_menu
from telechargeur import verifier_ffmpeg

def verifier_ffmpeg():
    """
    Vérifie que ffmpeg est disponible, et tente de le télécharger si absent.
    """
    print("🔍 Vérification de ffmpeg...")
    try:
        import imageio_ffmpeg
        chemin = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"✅ ffmpeg trouvé : {chemin}")
        return True
    except Exception as e:
        print("❌ ffmpeg n'a pas pu être installé automatiquement.")
        print(f"   Détail : {e}")
        print("\n💡 Solutions possibles :")
        print("   1. Vérifie ta connexion internet et relance le programme")
        print("   2. Installe ffmpeg manuellement : https://ffmpeg.org/download.html")
        print("      puis ajoute-le à ta variable d'environnement PATH")
        return False


def main():
    # Pour l'instant, on lance toujours le menu interactif.
    # (On pourra ajouter argparse ici plus tard si besoin
    # d'un mode "ligne de commande" en plus du menu)
    if not verifier_ffmpeg():
        input("\nAppuie sur Entrée pour quitter...")
    lancer_menu()


if __name__ == "__main__":
    main()

