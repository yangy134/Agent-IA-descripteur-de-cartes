"""
BENCHMARK OFFICIEL ULTIME ACCÉLÉRÉ (MULTITHREADING PARALLÈLE) SUR 9 CARTES MULTI-FOURNISSEURS :
- Extraction Spatial + Voirie en PARALLÈLE (comme dans le vrai src/chain.py)
- Délibération des 3 Juges en PARALLÈLE
-> Temps de traitement divisé par 3 !
"""

import os
import sys
import time
import json
import re
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

from src.chain import CollaborativeMapPipeline
from src.collaborative_prompts import (
    PROMPT_SPATIAL_EXTRACTOR as FINAL_SPATIAL,
    PROMPT_STREETS_EXTRACTOR as FINAL_STREETS,
    PROMPT_ARBITER_SYNTHESIS as FINAL_ARBITER,
    PROMPT_JURY_EVALUATOR
)
from src.prompts_backup_initial import (
    PROMPT_SPATIAL_EXTRACTOR_INITIAL as OLD_SPATIAL,
    PROMPT_STREETS_EXTRACTOR_INITIAL as OLD_STREETS,
    PROMPT_ARBITER_SYNTHESIS_INITIAL as OLD_ARBITER
)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

NINE_MAPS = [
    {"name": "GoogleMaps_Map1", "path": "maps/google_maps/Map1_GoogleMaps.png"},
    {"name": "GoogleMaps_Map2", "path": "maps/google_maps/Map2_GoogleMaps.png"},
    {"name": "GoogleMaps_Map3", "path": "maps/google_maps/Map3_GoogleMaps.png"},
    {"name": "AppleMaps_Map1", "path": "maps/apple_maps/Map1_AppleMaps.png"},
    {"name": "AppleMaps_Map2", "path": "maps/apple_maps/Map2_AppleMaps.png"},
    {"name": "AppleMaps_Map3", "path": "maps/apple_maps/Map3_AppleMaps.png"},
    {"name": "OSM_Map1", "path": "maps/osm/Map1_Osm.png"},
    {"name": "OSM_Map2", "path": "maps/osm/Map2_Osm.png"},
    {"name": "OSM_Map3", "path": "maps/osm/Map3_Osm.png"},
]

MODEL_SPATIAL = "qwen/qwen-2.5-vl-72b-instruct"
MODEL_STREETS = "google/gemma-3-27b-it"
MODEL_ARBITER = "meta-llama/llama-4-scout"

JURY = [
    {"name": "Juge_Qwen", "model": "qwen/qwen-2.5-vl-72b-instruct"},
    {"name": "Juge_Gemma", "model": "google/gemma-3-27b-it"},
    {"name": "Juge_Llama", "model": "meta-llama/llama-4-scout"}
]

def parse_jury_note(eval_text: str) -> float:
    match = re.search(r"NOTE\s*:\s*\[?(\d+(?:\.\d+)?)\s*/\s*10\]?", eval_text, re.IGNORECASE)
    return float(match.group(1)) if match else 7.0

def generate_pipeline_fast(pipeline: CollaborativeMapPipeline, image_path: str, p_spatial: str, p_streets: str, p_arbiter: str) -> str:
    image_url = pipeline._encode_image(image_path)
    
    # ⚡ Extractions Spatiale et Voirie EN PARALLÈLE
    with ThreadPoolExecutor(max_workers=2) as executor:
        f_spatial = executor.submit(pipeline._call_vlm, MODEL_SPATIAL, p_spatial, image_url, max_tokens=800)
        f_streets = executor.submit(pipeline._call_vlm, MODEL_STREETS, p_streets, image_url, max_tokens=800)
        spatial_out = f_spatial.result()
        streets_out = f_streets.result()
        
    arbiter_input = p_arbiter.format(spatial_report=spatial_out, streets_report=streets_out)
    final_desc = pipeline._call_vlm(MODEL_ARBITER, arbiter_input, image_url, max_tokens=800)
    return final_desc

def evaluate_with_jury_fast(pipeline: CollaborativeMapPipeline, description: str, image_path: str, label_prefix: str, output_dir: str) -> dict:
    image_url = pipeline._encode_image(image_path)
    eval_prompt = PROMPT_JURY_EVALUATOR.format(candidate_description=description)
    
    def call_judge(j):
        name = j["name"]
        model = j["model"]
        report = pipeline._call_vlm(model, eval_prompt, image_url, max_tokens=600)
        note = parse_jury_note(report)
        with open(os.path.join(output_dir, f"{label_prefix}_{name}.txt"), "w", encoding="utf-8") as f:
            f.write(report)
        return name, note, report

    # ⚡ Délibération des 3 juges EN PARALLÈLE
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(call_judge, JURY))
        
    scores = {name: note for name, note, _ in results}
    reports = {name: report for name, _, report in results}
    avg = round(sum(scores.values()) / len(scores), 2)
    return {"scores": scores, "avg": avg, "reports": reports}

def main():
    pipeline = CollaborativeMapPipeline()
    output_dir = "outputs/benchmark_ultime_9_maps"
    os.makedirs(output_dir, exist_ok=True)
    
    old_baseline_file = "outputs/benchmark_9_maps/benchmark_summary_progress.json"
    old_data = {}
    if os.path.exists(old_baseline_file):
        with open(old_baseline_file, "r", encoding="utf-8") as f:
            old_data = json.load(f).get("old_prompts", {})
            
    summary_file = os.path.join(output_dir, "benchmark_summary_progress.json")
    summary = {
        "old_prompts": old_data,
        "final_prompts": {}
    }
    if os.path.exists(summary_file):
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                summary = json.load(f)
        except Exception:
            pass

    print("=" * 85)
    print("⚡ GRAND BENCHMARK ULTIME ULTRA-RAPIDE (PARALLÈLE) SUR 9 CARTES")
    print("Baseline (Anciens Prompts) VS Version Finale Optimisée (Anti-Hallucination Strict)")
    print("=" * 85)
    
    for idx, m in enumerate(NINE_MAPS, 1):
        map_name = m["name"]
        map_path = m["path"]
        print(f"\n[{idx}/9] >>> CARTE : {map_name} <<<")
        
        # 1. Baseline anciens prompts
        if map_name in summary["old_prompts"]:
            old_score = summary["old_prompts"][map_name]["avg"]
            print(f"  📌 Score Baseline Anciens Prompts : {old_score}/10")
        else:
            print(f"  [Anciens] Exécution...")
            desc_old = generate_pipeline_fast(pipeline, map_path, OLD_SPATIAL, OLD_STREETS, OLD_ARBITER)
            eval_old = evaluate_with_jury_fast(pipeline, desc_old, map_path, f"{map_name}_OLD", output_dir)
            summary["old_prompts"][map_name] = {"avg": eval_old["avg"], "scores": eval_old["scores"]}
            old_score = eval_old["avg"]
            print(f"  📌 Score Baseline Anciens Prompts : {old_score}/10")
            
        # 2. Version Finale
        if map_name not in summary["final_prompts"]:
            print(f"  🚀 [V_FINALE] Exécution accélérée...")
            t0 = time.time()
            desc_final = generate_pipeline_fast(pipeline, map_path, FINAL_SPATIAL, FINAL_STREETS, FINAL_ARBITER)
            t_gen = round(time.time() - t0, 1)
            
            with open(os.path.join(output_dir, f"{map_name}_FINAL_desc.txt"), "w", encoding="utf-8") as f:
                f.write(desc_final)
                
            print(f"  -> Généré en {t_gen}s ! Délibération simultanée des 3 Juges...")
            t_eval = time.time()
            eval_final = evaluate_with_jury_fast(pipeline, desc_final, map_path, f"{map_name}_FINAL", output_dir)
            print(f"  -> Jugé en {round(time.time() - t_eval, 1)}s !")
            
            summary["final_prompts"][map_name] = {
                "time_s": t_gen,
                "avg": eval_final["avg"],
                "scores": eval_final["scores"]
            }
            print(f"  ⭐ Score V_FINALE : {eval_final['avg']}/10 {eval_final['scores']}")
            
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        else:
            print(f"  ✅ [V_FINALE] Déjà calculé : {summary['final_prompts'][map_name]['avg']}/10")
            
        diff = round(summary["final_prompts"][map_name]["avg"] - summary["old_prompts"][map_name]["avg"], 2)
        print(f"  📊 Bilan {map_name} : {summary['final_prompts'][map_name]['avg']}/10 vs {summary['old_prompts'][map_name]['avg']}/10 (Écart : {diff:+})")

    # Bilan récapitulatif
    print("\n" + "=" * 90)
    print("BILAN SCIENTIFIQUE COMPARATIF FINAL : 9 CARTES")
    print("=" * 90)
    print(f"{'Fournisseur':<12} | {'Carte':<18} | {'Anciens (/10)':<15} | {'V_Finale (/10)':<15} | {'Écart'}")
    print("-" * 90)
    
    old_list = []
    final_list = []
    for m in NINE_MAPS:
        k = m["name"]
        fournisseur = "Google" if "Google" in k else ("Apple" if "Apple" in k else "OSM")
        s_old = summary["old_prompts"][k]["avg"]
        s_fin = summary["final_prompts"][k]["avg"]
        old_list.append(s_old)
        final_list.append(s_fin)
        diff = round(s_fin - s_old, 2)
        diff_str = f"+{diff}" if diff > 0 else f"{diff}"
        print(f"{fournisseur:<12} | {k:<18} | {s_old:>8.2f} / 10   | {s_fin:>8.2f} / 10   | {diff_str:>6}")
        
    avg_old = round(sum(old_list) / len(old_list), 2)
    avg_fin = round(sum(final_list) / len(final_list), 2)
    diff_total = round(avg_fin - avg_old, 2)
    diff_total_str = f"+{diff_total}" if diff_total > 0 else f"{diff_total}"
    
    print("-" * 90)
    print(f"{'MOYENNE GLOBALE':<32} | {avg_old:>8.2f} / 10   | {avg_fin:>8.2f} / 10   | {diff_total_str:>6}")
    print("=" * 90)
    
    with open(os.path.join(output_dir, "RAPPORT_FINAL.txt"), "w", encoding="utf-8") as f:
        f.write(f"MOYENNE ANCIENS PROMPTS : {avg_old}/10\n")
        f.write(f"MOYENNE V_FINALE        : {avg_fin}/10\n")
        f.write(f"PROGRESSION TOTALE      : {diff_total_str}\n\n")
        f.write(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
