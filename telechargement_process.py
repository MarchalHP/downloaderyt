"""
Script exécuté dans une fenêtre de terminal séparée.
Lance les téléchargements et affiche une barre de progression.
La fenêtre se ferme automatiquement une fois terminé.
"""
import sys
import json
import os
import time
from telechargeur import telecharger_une_tache
from progression import (
    initialiser_progression,
    mettre_a_jour_progression,
    nettoyer_progression
)


def afficher_barre(actuel, total, largeur=40):
    """Affiche une barre de progression texte."""
    pourcentage = actuel / total if total > 0 else 0
    remplissage = int(largeur * pourcentage)
    barre = "█" * remplissage + "░" * (largeur - remplissage)
    print(f"\r[{barre}] {actuel}/{total} ({pourcentage*100:.1f}%)", end="", flush=True)


def main():
    fichier_taches = sys.argv[1]
    fichier_config = sys.argv[2]

    with open(fichier_taches, "r", encoding="utf-8") as f:
        taches = json.load(f)
    with open(fichier_config, "r", encoding="utf-8") as f:
        config = json.load(f)

    total = len(taches)
    initialiser_progression(total)

    print("=" * 50)
    print("  TÉLÉCHARGEMENT EN COURS (fenêtre dédiée)")
    print("=" * 50)
    print(f"\n📋 {total} tâche(s) à traiter.\n")

    dossier_de_base = config.get('dossier_sortie_defaut', 'downloads')
    reussites = 0
    echecs = 0

    for i, tache in enumerate(taches, start=1):
        url = tache["url"]
        dossier_tache = tache.get('dossier', '')
        if dossier_tache and dossier_tache != dossier_de_base:
            dossier_cible = os.path.join(dossier_de_base, dossier_tache) \
                if not os.path.isabs(dossier_tache) else dossier_tache
        else:
            dossier_cible = dossier_de_base

        mettre_a_jour_progression(tache_actuelle=i, nom_tache=url)
        print(f"\n--- Tâche {i}/{total} ---")
        print(f"🔗 {url}")

        afficher_barre(i - 1, total)

        succes, fichiers_crees = telecharger_une_tache(
            tache, dossier_cible, config, retourner_fichiers=True
        )

        if succes:
            reussites += 1
            for fichier in fichiers_crees:
                mettre_a_jour_progression(nouveau_fichier=fichier)
        else:
            echecs += 1

        afficher_barre(i, total)

    mettre_a_jour_progression(termine=True)

    print("\n\n" + "=" * 50)
    print("📊 RÉSUMÉ")
    print("=" * 50)
    print(f"✅ Réussites : {reussites}")
    print(f"❌ Échecs    : {echecs}")
    print("\n✅ Téléchargement terminé.")
    print("🚪 Fermeture automatique de cette fenêtre dans 5 secondes...")

    time.sleep(5)  # ⬅️ Laisse le temps de lire le résumé avant fermeture


if __name__ == "__main__":
    main()