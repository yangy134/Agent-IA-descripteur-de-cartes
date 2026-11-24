"""
Point d'entrée principal pour générer une description accessible de carte.
Utilise l'architecture championne C1 (Qwen Spatial + Gemma Voirie -> Llama Synthèse).
"""

import os
import sys
import argparse
from src.chain import CollaborativeMapPipeline

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="GeoAI-Carto : Description accessible de centre-ville pour malvoyants")
    parser.add_argument("--image", type=str, default=None, help="Chemin vers l'image de la carte (laisser vide pour saisir)")
    parser.add_argument("--output-dir", type=str, default="outputs", help="Dossier de sortie pour la description")
    args = parser.parse_args()

    # Si le chemin n'est pas fourni en ligne de commande, demander interactivement
    if not args.image:
        args.image = input("Veuillez saisir le chemin complet vers l'image de la carte : ").strip()

    if not os.path.exists(args.image):
        print(f"[ERREUR] Fichier introuvable : {args.image}")
        print("Usage : python main.py --image <chemin/vers/votre_carte.png>")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    filename = os.path.basename(args.image)
    base_name = os.path.splitext(filename)[0]

    print("==================================================================")
    print("GEOAI-CARTO : GÉNÉRATION ACCESSIBLE (ARCHITECTURE C1)")
    print("==================================================================")
    print(f"Image cible : {args.image}")

    pipeline = CollaborativeMapPipeline()
    result = pipeline.run(args.image)

    output_path = os.path.join(args.output_dir, f"{base_name}_accessible_desc.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result["final_description"])

    print("\n" + "=" * 65)
    print(f"DESCRIPTION ACCESSIBLE GÉNÉRÉE : {filename}")
    print("=" * 65)
    print(result["final_description"])
    print("=" * 65)
    print(f"[OK] Description sauvegardée dans : {output_path}")

if __name__ == "__main__":
    main()
