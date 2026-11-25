"""
Module formatage_resultat_final.py (Conforme au schéma de Marie).
Prend la meilleure description validée après la boucle d'auto-correction
et génère le livrable final : Description_finale.txt.
"""

import os
from pathlib import Path

def sauvegarder_description_finale(chemin_execution: str, description_finale: str, nom_carte: str = None) -> str:
    """
    Enregistre la description finale retenue dans le dossier d'exécution.
    """
    chemin_data_sorties = os.path.join(chemin_execution, "data_sorties")
    os.makedirs(chemin_data_sorties, exist_ok=True)

    nom_fichier = "Description_finale.txt" if not nom_carte else f"{nom_carte}_Description_finale.txt"
    chemin_fichier = os.path.join(chemin_data_sorties, nom_fichier)

    with open(chemin_fichier, "w", encoding="utf-8") as f:
        f.write(description_finale.strip())

    print(f"[OK] Description finale enregistrée : {chemin_fichier}")
    return chemin_fichier

if __name__ == "__main__":
    test_dir = "test_exec"
    os.makedirs(os.path.join(test_dir, "data_sorties"), exist_ok=True)
    f = sauvegarder_description_finale(test_dir, "Contenu description finale.", "CarteTest")
    os.remove(f)
    os.rmdir(os.path.join(test_dir, "data_sorties"))
    os.rmdir(test_dir)
