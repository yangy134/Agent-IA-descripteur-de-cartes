"""
Module generer_reponses_IA.py (Conforme au schéma de Marie).
Encapsule le Programme de Mehdi : génération collaborative de description cartographique
par la chaîne triple-VLM (Qwen repère spatial + Gemma voirie fine -> Llama arbitre de synthèse).
"""

import os
import sys
import time
from src.chain import CollaborativeMapPipeline, MODEL_SPATIAL, MODEL_STREETS, MODEL_ARBITER

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def generer_reponse_initiale(image_path: str, pipeline: CollaborativeMapPipeline = None) -> dict:
    """
    Exécute le Programme de Mehdi (Chaîne C1) sur la carte spécifiée.

    Parameters:
    -----------
    image_path : str
        Chemin vers l'image de la carte.
    pipeline : CollaborativeMapPipeline, optional
        Instance du pipeline (si déjà instancié).

    Returns:
    --------
    dict: Contient la description générée, les temps d'exécution et les métadonnées.
    """
    if not pipeline:
        pipeline = CollaborativeMapPipeline()

    t0 = time.time()
    resultats = pipeline.run(image_path)
    duree = round(time.time() - t0, 1)

    return {
        "description": resultats["final_description"],
        "duree_secondes": duree,
        "spatial_raw": resultats.get("spatial_raw", ""),
        "roads_raw": resultats.get("roads_raw", ""),
        "modeles": {
            "spatial": MODEL_SPATIAL,
            "voirie": MODEL_STREETS,
            "arbitre": MODEL_ARBITER
        }
    }

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    res = generer_reponse_initiale("maps/google_maps/Map1_GoogleMaps.png")
    print("\n--- TEST GÉNÉRATION INITIALE RÉUSSI ---")
    print(f"Durée : {res['duree_secondes']}s")
    print(f"Longueur description : {len(res['description'])} caractères")
