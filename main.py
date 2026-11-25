"""
Point d'entrée principal pour générer une description accessible de carte.
Intègre la boucle d'auto-correction complète conforme aux travaux et schémas de Marie :
- Création du dossier d'exécution officiel (creation_dossier_execution.py)
- Programme de Mehdi C1 (Qwen Spatial + Gemma Voirie -> Llama Synthèse)
- Formatage automatique des sorties JSON (formatage_sorties.py)
- Audit et notation de conformité cartographique (analyse_score.py)
- Boucle d'auto-correction avec seuil et convergence (arret_et_redirection.py)
- Livrable final Description_finale.txt (formatage_resultat_final.py)
"""

import os
import sys
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from src.chain import CollaborativeMapPipeline
from scripts_marie.arret_et_redirection import executer_boucle_autocorrection

def main():
    parser = argparse.ArgumentParser(description="GeoAI-Carto : Agent IA descripteur de cartes pour déficients visuels")
    parser.add_argument("--image", type=str, default=None, help="Chemin vers l'image de la carte")
    parser.add_argument("--seuil", type=float, default=9.0, help="Note minimale sur 10 pour valider sans relance (défaut : 9.0)")
    parser.add_argument("--max-tours", type=int, default=2, help="Nombre maximal de tours d'auto-correction (défaut : 2)")
    args = parser.parse_args()

    # Saisie interactive si aucun chemin n'est fourni
    if not args.image:
        args.image = input("Veuillez saisir le chemin de la carte à décrire : ").strip().strip('"').strip("'")
    else:
        args.image = args.image.strip('"').strip("'")

    if not os.path.exists(args.image):
        print(f"[ERREUR] Image introuvable : {args.image}")
        print("Usage : python main.py --image <chemin/vers/carte.png>")
        sys.exit(1)

    print("==================================================================")
    print("GEOAI-CARTO : CHAÎNE DE PRODUCTION AVEC AUTO-CORRECTION (MARIE & MEHDI)")
    print("==================================================================")
    print(f"Image cible : {args.image}")

    pipeline = CollaborativeMapPipeline()
    resultat = executer_boucle_autocorrection(
        image_path=args.image,
        seuil_arret=args.seuil,
        max_tours=args.max_tours,
        pipeline=pipeline
    )

    print("\n" + "=" * 75)
    print(f"DESCRIPTION FINALE POUR LECTEUR D'ÉCRAN : {resultat['carte']}")
    print(f"Note finale certifiée : {resultat['note_finale']}/10 (en {resultat['nombre_tours']} tour(s))")
    print("=" * 75)
    print(resultat["description_finale"])
    print("=" * 75)
    print(f"[OK] Dossier d'exécution complet : {resultat['dossier_exec']}")
    print(f"[OK] Fichier final : {resultat['fichier_final']}")

if __name__ == "__main__":
    main()
