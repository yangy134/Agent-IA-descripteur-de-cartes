"""
Pipeline Collaboratif Multi-IA avec Boucle d'Audit et d'Auto-Correction.
- Agent 1 : Qwen 2.5-VL 72B (Extraction spatiale et repères)
- Agent 2 : Gemma 3 27B (Voirie fine et décodage d'abréviations)
- Agent 3 : Llama 4 Scout (Arbitre de consensus)
- Agent 4 : Qwen 2.5-VL 72B (Auditeur qualité & calcul de la note)
- Agent 5 : Llama 4 Scout (Correcteur ciblé si note < 8/10)
"""

import os
import re
import time
import base64
import requests
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from src.collaborative_prompts import (
    PROMPT_SPATIAL_EXTRACTOR,
    PROMPT_STREETS_EXTRACTOR,
    PROMPT_ARBITER_SYNTHESIS,
    PROMPT_EVALUATOR,
    PROMPT_CORRECTION
)

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_SPATIAL = "qwen/qwen-2.5-vl-72b-instruct"    # Alibaba : Extraction macro
MODEL_STREETS = "google/gemma-3-27b-it"             # Google : Voirie & abréviations
MODEL_ARBITER = "meta-llama/llama-4-scout"          # Meta : Arbitre initial
MODEL_EVALUATOR = "qwen/qwen-2.5-vl-72b-instruct"  # Alibaba : Auditeur / Contrôleur de vérité terrain
MODEL_CORRECTOR = "meta-llama/llama-4-scout"        # Meta : Rédacteur de correction

class CollaborativeMapPipeline:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY introuvable dans .env")

    def _encode_image(self, image_path: str) -> str:
        ext = os.path.splitext(image_path)[1].lower().replace(".", "")
        mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{b64}"

    def _call_vlm(self, model: str, prompt: str, image_url: str, max_tokens: int = 800, retries: int = 6) -> str:
        import time
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/geoai-carto",
            "X-Title": "GeoAI Collaborative Chain",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1
        }

        last_error = None
        for attempt in range(1, retries + 1):
            try:
                time.sleep(2)
                response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=90)
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                elif response.status_code in [429, 502, 503, 504]:
                    wait_time = 12
                    print(f"  [Tentative {attempt}/{retries}] Statut {response.status_code} (Rate Limit), pause de {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise RuntimeError(f"Erreur API ({response.status_code}) avec {model}: {response.text}")
            except Exception as e:
                last_error = e
                print(f"  [Tentative {attempt}/{retries}] Incident réseau/DNS ({e}), pause de 10s...")
                time.sleep(10)

        raise RuntimeError(f"Échec après {retries} tentatives sur {model} : {last_error}")

    def parse_evaluation(self, eval_text: str) -> tuple[float, str]:
        # Extraction de la note (ex: NOTE: [8.5/10] ou NOTE: 8/10)
        note = 7.0
        match_note = re.search(r"NOTE\s*:\s*\[?(\d+(?:\.\d+)?)\s*/\s*10\]?", eval_text, re.IGNORECASE)
        if match_note:
            note = float(match_note.group(1))

        # Extraction de la décision
        decision = "A_CORRIGER"
        if "VALIDE" in eval_text.upper() and note >= 8.0:
            decision = "VALIDE"

        return note, decision

    def run(self, image_path: str, use_spatial: bool = True, use_streets: bool = True,
            model_spatial: str = None, model_streets: str = None, model_arbiter: str = None) -> dict:
        filename = os.path.basename(image_path)
        m_spatial = model_spatial or MODEL_SPATIAL
        m_streets = model_streets or MODEL_STREETS
        m_arbiter = model_arbiter or MODEL_ARBITER

        print(f"\n==================================================")
        print(f"LANCEMENT DE LA CHAÎNE ZERO-SHOT : {filename}")
        print(f"Modèles : Spatial={m_spatial} | Voirie={m_streets} | Arbitre={m_arbiter}")
        print(f"==================================================")

        image_url = self._encode_image(image_path)

        start_time = time.time()
        spatial_report = "Aucun rapport spatial fourni (Agent désactivé pour ablation)."
        streets_report = "Aucun rapport de voirie fourni (Agent désactivé pour ablation)."

        # Étape 1 & 2 : Extraction parallèle (Spatial + Voirie)
        if use_spatial and use_streets:
            print(f"\n[1 & 2 / 3] Lancement EN PARALLÈLE des Agents d'extraction :")
            print(f"  ⚡ Agent Spatial ({m_spatial})")
            print(f"  ⚡ Agent Voirie   ({m_streets})")
            t_extract_start = time.time()
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_spatial = executor.submit(self._call_vlm, m_spatial, PROMPT_SPATIAL_EXTRACTOR, image_url)
                future_streets = executor.submit(self._call_vlm, m_streets, PROMPT_STREETS_EXTRACTOR, image_url)
                spatial_report = future_spatial.result()
                streets_report = future_streets.result()
            print(f"-> [OK] Extractions spatiales et de voirie terminées en {time.time() - t_extract_start:.1f}s.")
        elif use_spatial:
            print(f"\n[1/3] Agent Spatial ({m_spatial}) : Inventaire macro et repères...")
            spatial_report = self._call_vlm(m_spatial, PROMPT_SPATIAL_EXTRACTOR, image_url)
            print("-> Rapport spatial généré.")
        elif use_streets:
            print(f"\n[2/3] Agent Voirie ({m_streets}) : Extraction des rues & abréviations...")
            streets_report = self._call_vlm(m_streets, PROMPT_STREETS_EXTRACTOR, image_url)
            print("-> Rapport de voirie généré.")

        # Étape 3 : Arbitre de Synthèse
        print(f"\n[3/3] Arbitre de Synthèse ({m_arbiter}) : Rédaction de la description finale (zero-shot)...")
        t_arbiter_start = time.time()
        arbiter_prompt = PROMPT_ARBITER_SYNTHESIS.format(
            spatial_report=spatial_report,
            streets_report=streets_report
        )
        final_description = self._call_vlm(m_arbiter, arbiter_prompt, image_url)
        print(f"-> Description finale zero-shot produite en {time.time() - t_arbiter_start:.1f}s.")
        print(f"⏱️ Temps total de génération : {time.time() - start_time:.1f}s.")

        # =========================================================================
        # CODE DE CORRECTION ET D'AUDIT (MIS EN COMMENTAIRE POUR PLUS TARD SELON CONSIGNE DU PROF)
        # =========================================================================
        # # Étape 4 : Évaluation & Audit (Qwen 2.5-VL 72B)
        # print("\n[4/5] Auditeur Qualité (Qwen 2.5-VL 72B) : Contrôle de fidélité et attribution de note...")
        # eval_prompt = PROMPT_EVALUATOR.format(candidate_description=current_description)
        # eval_report = self._call_vlm(MODEL_EVALUATOR, eval_prompt, image_url)
        # note, decision = self.parse_evaluation(eval_report)
        # print(f"-> Résultat de l'Audit : Note = {note}/10 | Décision = {decision}")
        #
        # # Étape 5 : Boucle de Correction si la note est insuffisante (< 8/10)
        # if decision == "A_CORRIGER" and max_retries > 0:
        #     print("\n[5/5] ⚠️ Note < 8/10 ou erreurs détectées : Déclenchement de la boucle de correction !")
        #     correction_prompt = PROMPT_CORRECTION.format(
        #         candidate_description=current_description,
        #         feedback=eval_report
        #     )
        #     current_description = self._call_vlm(MODEL_CORRECTOR, correction_prompt, image_url)
        #     re_eval_prompt = PROMPT_EVALUATOR.format(candidate_description=current_description)
        #     final_eval_report = self._call_vlm(MODEL_EVALUATOR, re_eval_prompt, image_url)
        #     note_finale, decision_finale = self.parse_evaluation(final_eval_report)
        # =========================================================================

        return {
            "spatial_report": spatial_report,
            "streets_report": streets_report,
            "final_description": final_description
        }
