"""
Module construction_prompts.py (Conforme au schéma de Marie).
Construit les prompts révisés (PromptV2) en utilisant :
- base_prompts.txt (règles génériques anti-hallucination)
- Les scores et anomalies détectées par analyse_score.py
- La description issue du tour précédent
"""

import os
from pathlib import Path

def charger_base_prompts() -> str:
    """Charge le fichier base_prompts.txt défini dans le schéma de Marie."""
    chemin_base = Path(__file__).parent / "base_prompts.txt"
    if chemin_base.exists():
        with open(chemin_base, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def construire_prompt_correction(ancienne_description: str, erreurs_detectees: str) -> str:
    """
    Construit le prompt de correction (PromptV2) en injectant la base de prompts,
    l'ancienne description et les erreurs relevées par l'auditeur.
    """
    base_contexte = charger_base_prompts()

    prompt = f"""Tu es l'Arbitre cartographique en charge de l'auto-correction de la description pour personnes déficientes visuelles.

--- CONTEXTE ET RÈGLES GÉNÉRALES ---
{base_contexte}

--- DESCRIPTION DU TOUR PRÉCÉDENT ---
{ancienne_description.strip()}

--- ERREURS ET ANOMALIES IDENTIFIÉES PAR L'ÉVALUATION ---
{erreurs_detectees.strip()}

--- MISSION DE CORRECTION ---
En regardant attentivement l'image de la carte fournie :
1. Corrige immédiatement chaque anomalie signalée ci-dessus (orthographe exacte des rues, suppression des éléments inventés/non visibles, rectification des orientations).
2. Ne conserve que ce qui est 100% visible et attesté sur l'image de la carte.
3. Conserve la structure claire :
   - ## VUE D'ENSEMBLE
   - ## AXES ET VOIRIE
   - ## REPÈRES REMARQUABLES
   - ## POINTS D'INCERTITUDE

Rédige directement la description corrigée finale en français.
"""
    return prompt

if __name__ == "__main__":
    p = construire_prompt_correction("Description V1...", "- Rue de Passy est mal orientée.")
    print("Prompt de correction généré avec succès.")
