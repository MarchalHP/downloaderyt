"""
Point d'entrée du programme.
- Si lancé sans argument (double-clic) → ouvre le menu interactif
- Si lancé avec des arguments en ligne de commande → mode direct (optionnel)
"""

import sys
from menu import lancer_menu


def main():
    # Pour l'instant, on lance toujours le menu interactif.
    # (On pourra ajouter argparse ici plus tard si besoin
    # d'un mode "ligne de commande" en plus du menu)
    lancer_menu()


if __name__ == "__main__":
    main()

