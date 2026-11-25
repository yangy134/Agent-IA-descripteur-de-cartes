"""
Module arret_et_redirection.py (Conforme au schéma de Marie).
Gère la boucle d'auto-correction complète :
1. Crée le dossier d'exécution via creation_dossier_execution.py (Marie).
2. Lance generer_reponses_IA.py (Programme de Mehdi C1) pour le Tour 1.
3. Sauvegarde la réponse brute avec le nommage officiel de Marie :
   {NomCarte}_{NomLLM}_{NbTour}_{NbRepetitionPrompt}_{NbPrompt}_ReponseBrute.txt
4. Formate les sorties en JSON via formatage_sorties.py (Marie).
5. Évalue le score et les anomalies via analyse_score.py (Qwen).
6. Vérifie la condition d'arrêt selon les 2 méthodes prévues par Marie :
   - Méthode A : Seuil de note atteint (ex: >= 9.0/10) ou limite de tours (ex: 2)
   - Méthode B : Convergence des sorties (ressemblance textuelle/sémantique au-dessus d'un seuil)
7. Si arrêt non respecté :
   - Appelle construction_prompts.py (base_prompts.txt + erreurs)
   - Relance le modèle correcteur pour le Tour suivant
   - Re-formate avec formatage_sorties.py
8. À l'arrêt :
   - Enregistre Description_finale.txt via formatage_resultat_final.py
   - Met à jour metadonnees_execution.txt et liste_executions.txt.
"""

import os
import sys
import time
import json
import re
import difflib
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.chain import CollaborativeMapPipeline
from scripts_marie.creation_dossier_execution import crea_doss_exec
from scripts_marie.formatage_sorties import formatage_sorties
from scripts_marie.generer_reponses_IA import generer_reponse_initiale
from scripts_marie.analyse_score import evaluer_description
from scripts_marie.construction_prompts import construire_prompt_correction
from scripts_marie.formatage_resultat_final import sauvegarder_description_finale

MODEL_CORRECTEUR = "meta-llama/llama-4-scout"

# Mots vides français selon l'indication textuelle de Marie : "(les, le, des...)"
MOTS_VIDES = {
    "le", "la", "les", "de", "du", "des", "un", "une", "d", "l",
    "et", "en", "a", "à", "dans", "par", "pour", "sur", "au", "aux",
    "ce", "cette", "ces", "qui", "que", "est", "sont", "avec", "sans",
    "y", "ne", "pas", "se", "sa", "son", "ses"
}

def assainir_nom_carte(chemin_image: str) -> str:
    """
    Extrait un nom de carte compatible avec le découpage par '_' de Marie.
    Les tirets bas internes sont retirés pour que tab_meta[0] corresponde au nom complet.
    """
    nom_base = os.path.splitext(os.path.basename(chemin_image))[0]
    return nom_base.replace("_", "")

def mesurer_convergence_semantique(texte_precedent: str, texte_nouveau: str) -> dict:
    """
    Mesure la convergence entre deux versions successives selon la proposition de Marie :
    - Analyse sémantique en retirant les mots 'inutiles' (mots vides)
    - Comptage des mots en commun et des mots exclus
    - Mesure de distance séquentielle (Levenshtein / SequenceMatcher).
    """
    mots_prec = set(re.findall(r"\b\w+\b", texte_precedent.lower())) - MOTS_VIDES
    mots_nouv = set(re.findall(r"\b\w+\b", texte_nouveau.lower())) - MOTS_VIDES

    mots_communs = mots_prec.intersection(mots_nouv)
    union_mots = mots_prec.union(mots_nouv)

    similarite_jaccard = len(mots_communs) / len(union_mots) if union_mots else 1.0
    distance_levenshtein = difflib.SequenceMatcher(None, texte_precedent, texte_nouveau).ratio()

    return {
        "similarite_jaccard": round(similarite_jaccard, 3),
        "similarite_levenshtein": round(distance_levenshtein, 3),
        "mots_communs_count": len(mots_communs),
        "mots_nouveaux_count": len(mots_nouv - mots_prec)
    }

def executer_boucle_autocorrection(
    image_path: str,
    seuil_arret: float = 9.0,
    max_tours: int = 2,
    seuil_convergence: float = 0.95,
    pipeline: CollaborativeMapPipeline = None
) -> dict:
    """
    Exécute le cycle complet d'auto-correction selon le schéma d'architecture de Marie.
    """
    if not pipeline:
        pipeline = CollaborativeMapPipeline()

    nom_carte = assainir_nom_carte(image_path)
    nom_llm = "MehdiC1"

    print("\n" + "=" * 75)
    print(f"LANCEMENT DE LA BOUCLE D'AUTO-CORRECTION : {nom_carte}")
    print(f"Critères d'arrêt : Note >= {seuil_arret}/10 | Convergence >= {seuil_convergence*100}% | Max {max_tours} tour(s)")
    print("=" * 75)

    # Étape 1 : Création du dossier d'exécution officiel de Marie
    chemin_exec = crea_doss_exec()
    dossier_brut = os.path.join(chemin_exec, "data_reponses_brutes")
    dossier_sorties = os.path.join(chemin_exec, "data_sorties")

    historique = []
    tour = 1
    image_url = pipeline._encode_image(image_path)

    # --- TOUR 1 : Génération initiale par le Programme de Mehdi ---
    print(f"\n--- [TOUR 1/{max_tours}] GÉNERATION INITIALE (PROGRAMME DE MEHDI C1) ---")
    gen_t1 = generer_reponse_initiale(image_path, pipeline)
    current_desc = gen_t1["description"]

    # Sauvegarde selon la convention stricte de Marie
    nom_fichier_brut_t1 = f"{nom_carte}_{nom_llm}_1_1_1_ReponseBrute.txt"
    chemin_brut_t1 = os.path.join(dossier_brut, nom_fichier_brut_t1)
    with open(chemin_brut_t1, "w", encoding="utf-8") as f:
        f.write(current_desc)
    print(f"[OK] Réponse brute Tour 1 enregistrée : {nom_fichier_brut_t1}")

    # Formatage des sorties officiel de Marie (scripts_marie/formatage_sorties.py)
    formatage_sorties(chemin_exec)
    print(f"[OK] Formatage sorties JSON de Marie exécuté.")

    # Évaluation du Tour 1 par analyse_score.py (Qwen évaluateur)
    eval_t1 = evaluer_description(pipeline, current_desc, image_path)
    note_actuelle = eval_t1["note"]
    feedback_actuel = eval_t1["erreurs_texte"]
    erreurs_restantes = eval_t1["erreurs_liste"]

    historique.append({
        "tour": 1,
        "modele": nom_llm,
        "note": note_actuelle,
        "erreurs": erreurs_restantes,
        "duree_s": gen_t1["duree_secondes"]
    })

    # Mise à jour des métadonnées du Tour 1
    chemin_meta = os.path.join(chemin_exec, "metadonnees_execution.txt")
    with open(chemin_meta, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"MÉTADONNÉES D'EXÉCUTION : {os.path.basename(chemin_exec)}\n")
        f.write(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Carte : {nom_carte} ({image_path})\n")
        f.write("=" * 60 + "\n")
        f.write(f"\n[Tour 1] Note : {note_actuelle}/10 | Erreurs détectées : {len(erreurs_restantes)}\n")

    if note_actuelle >= seuil_arret or len(erreurs_restantes) == 0:
        motif_arret = f"Score d'excellence atteint au Tour 1 ({note_actuelle}/10 >= {seuil_arret})"
    else:
        motif_arret = "Limite de tours atteinte"

    # --- BOUCLE DE CORRECTION (arret_et_redirection.py) ---
    while tour < max_tours and note_actuelle < seuil_arret and len(erreurs_restantes) > 0:
        tour += 1
        print(f"\n--- [TOUR {tour}/{max_tours}] AUTO-CORRECTION (Note actuelle : {note_actuelle}/10) ---")

        # Construction du prompt de correction PromptV2 (construction_prompts.py)
        prompt_v2 = construire_prompt_correction(current_desc, feedback_actuel)

        t_corr = time.time()
        print(f"  [Correcteur] Révision ciblée par {MODEL_CORRECTEUR}...")
        description_corrigee = pipeline._call_vlm(MODEL_CORRECTEUR, prompt_v2, image_url, max_tokens=800)
        duree_corr = round(time.time() - t_corr, 1)

        # Mesure de convergence selon le schéma de Marie
        metrics_conv = mesurer_convergence_semantique(current_desc, description_corrigee)
        print(f"  -> Indice de convergence (Levenshtein : {metrics_conv['similarite_levenshtein']*100:.1f}%, Sémantique : {metrics_conv['similarite_jaccard']*100:.1f}%)")

        # Sauvegarde réponse brute Tour N (convention Marie)
        nom_fichier_brut_tn = f"{nom_carte}_{nom_llm}_{tour}_1_1_ReponseBrute.txt"
        chemin_brut_tn = os.path.join(dossier_brut, nom_fichier_brut_tn)
        with open(chemin_brut_tn, "w", encoding="utf-8") as f:
            f.write(description_corrigee)
        print(f"[OK] Réponse brute Tour {tour} enregistrée : {nom_fichier_brut_tn}")

        # Formatage JSON officiel de Marie
        formatage_sorties(chemin_exec)

        # Re-évaluation par analyse_score.py
        print(f"  [Auditeur] Évaluation de la version corrigée...")
        eval_corr = evaluer_description(pipeline, description_corrigee, image_path)

        gain = round(eval_corr["note"] - note_actuelle, 2)
        gain_str = f"+{gain}" if gain > 0 else f"{gain}"
        print(f"  -> Évolution de la note au Tour {tour} : {note_actuelle}/10 -> {eval_corr['note']}/10 ({gain_str})")

        current_desc = description_corrigee
        note_actuelle = eval_corr["note"]
        feedback_actuel = eval_corr["erreurs_texte"]
        erreurs_restantes = eval_corr["erreurs_liste"]

        historique.append({
            "tour": tour,
            "modele": MODEL_CORRECTEUR,
            "note": note_actuelle,
            "erreurs": erreurs_restantes,
            "convergence": metrics_conv,
            "duree_s": duree_corr
        })

        # Enregistrement métadonnées Tour N
        with open(chemin_meta, "a", encoding="utf-8") as f:
            f.write(f"\n[Tour {tour}] Note : {note_actuelle}/10 | Convergence Levenshtein : {metrics_conv['similarite_levenshtein']*100:.1f}%\n")

        # Vérification arrêt par convergence ou note
        if note_actuelle >= seuil_arret:
            motif_arret = f"Seuil de note atteint ({note_actuelle}/10 >= {seuil_arret})"
            break
        if metrics_conv["similarite_levenshtein"] >= seuil_convergence:
            motif_arret = f"Convergence textuelle atteinte ({metrics_conv['similarite_levenshtein']*100:.1f}% >= {seuil_convergence*100}%)"
            break

    # --- LIVRABLE FINAL (formatage_resultat_final.py) ---
    print("\n" + "=" * 75)
    print(f"ARRÊT DE LA BOUCLE ({motif_arret}) : Note finale = {note_actuelle}/10")
    print("=" * 75)

    fichier_final = sauvegarder_description_finale(chemin_exec, current_desc, nom_carte)

    # Mise à jour de liste_executions.txt
    chemin_liste = os.path.join("executions", "liste_executions.txt")
    with open(chemin_liste, "a", encoding="utf-8") as f:
        f.write(f"{os.path.basename(chemin_exec)} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {nom_carte} | Note: {note_actuelle}/10 | Tours: {tour}\n")

    # Finalisation des métadonnées
    with open(chemin_meta, "a", encoding="utf-8") as f:
        f.write(f"\nMotif d'arrêt : {motif_arret}\n")
        f.write(f"Note finale : {note_actuelle}/10\n")
        f.write(f"Nombre de tours total : {tour}\n")
        f.write(f"Livrable final : {fichier_final}\n")

    return {
        "carte": nom_carte,
        "dossier_exec": chemin_exec,
        "description_finale": current_desc,
        "note_initiale": historique[0]["note"],
        "note_finale": note_actuelle,
        "nombre_tours": tour,
        "motif_arret": motif_arret,
        "fichier_final": fichier_final,
        "historique": historique
    }

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    pipe = CollaborativeMapPipeline()
    res = executer_boucle_autocorrection("maps/google_maps/Map1_GoogleMaps.png", seuil_arret=9.0, max_tours=2, pipeline=pipe)
    print("Résultat final :", res["note_finale"])
