"""
Module analyse_score.py (Conforme au schéma de Marie).
Appelle le modèle évaluateur/auditeur pour auditer la description candidate,
lui attribuer une note officielle sur 10 et lister précisément les erreurs détectées.
"""

import os
import re
from src.chain import CollaborativeMapPipeline
from src.collaborative_prompts import PROMPT_JURY_EVALUATOR

MODEL_EVALUATEUR = "qwen/qwen-2.5-vl-72b-instruct"

def parse_score_et_erreurs(texte_evaluation: str) -> dict:
    """
    Extrait la note globale sur 10 et la liste des erreurs depuis le rapport de l'auditeur.
    """
    # Extraction de la note : ex NOTE: [8.5/10] ou NOTE: 8.5/10
    match_note = re.search(r"NOTE\s*:\s*\[?(\d+(?:\.\d+)?)\s*/\s*10\]?", texte_evaluation, re.IGNORECASE)
    note = float(match_note.group(1)) if match_note else 7.0

    # Extraction des erreurs
    erreurs = []
    match_erreurs = re.search(r"ERREURS\s*:\s*(.*?)(?=\Z|###)", texte_evaluation, re.DOTALL | re.IGNORECASE)
    if match_erreurs:
        bloc_erreurs = match_erreurs.group(1).strip()
        for ligne in bloc_erreurs.split("\n"):
            ligne_propre = ligne.strip().lstrip("-*•").strip()
            if ligne_propre and "aucune erreur" not in ligne_propre.lower():
                erreurs.append(ligne_propre)

    if not erreurs:
        erreurs_texte = "Aucune erreur majeure détectée."
    else:
        erreurs_texte = "\n".join([f"- {err}" for err in erreurs])

    return {
        "note": note,
        "erreurs_liste": erreurs,
        "erreurs_texte": erreurs_texte,
        "rapport_complet": texte_evaluation.strip()
    }

def evaluer_description(pipeline: CollaborativeMapPipeline, description: str, image_path: str, model_eval: str = None) -> dict:
    """
    Évalue la fidélité de la description par rapport à l'image via l'auditeur.

    Parameters:
    -----------
    pipeline : CollaborativeMapPipeline
        Instance de la chaîne (fournit _call_vlm et _encode_image).
    description : str
        Texte de la description à évaluer.
    image_path : str
        Chemin vers l'image de la carte.

    Returns:
    --------
    dict : {'note': float, 'erreurs_liste': list, 'erreurs_texte': str, 'rapport_complet': str}
    """
    m_eval = model_eval or MODEL_EVALUATEUR
    image_url = pipeline._encode_image(image_path)
    prompt = PROMPT_JURY_EVALUATOR.format(candidate_description=description)

    print(f"  [Auditeur] Audit de conformité par {m_eval}...")
    rapport_brut = pipeline._call_vlm(m_eval, prompt, image_url, max_tokens=600)
    resultats = parse_score_et_erreurs(rapport_brut)

    print(f"  -> Note attribuée : {resultats['note']}/10")
    if resultats['erreurs_liste']:
        print(f"  -> {len(resultats['erreurs_liste'])} point(s) d'attention relevé(s).")
    else:
        print("  -> Zéro anomalie détectée.")

    return resultats

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    pipe = CollaborativeMapPipeline()
    desc_test = "Paris 16ème. Rues : Bd Suchet. Repères : Tour Eiffel."
    carte_test = "maps/google_maps/Map1_GoogleMaps.png"
    res = evaluer_description(pipe, desc_test, carte_test)
    print("Test scoring réussi :", res["note"], res["erreurs_liste"])
