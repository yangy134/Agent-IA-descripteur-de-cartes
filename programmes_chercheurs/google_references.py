import spacy
from spacy.matcher import Matcher
import json
import pandas as pd
import math
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from dataclasses import dataclass


def analyze_text(text):
    # Charger le modèle linguistique SpaCy
    nlp = spacy.load("en_core_web_md")

    # Créer un objet Matcher
    matcher = Matcher(nlp.vocab)

    # Utilisation de l'attribut LEMMA
    pattern = [{"TEXT": {"REGEX": "(?i)google"}}]  # Case-insensitive
    matcher.add("(?i)google", [pattern])

    # Traiter le texte avec SpaCy (cette étape calcule les lemmes !)
    doc = nlp(text)

    # Appliquer le Matcher au Doc pour trouver les correspondances
    matches = matcher(doc)

    return matches, doc

def display_results(matches, doc):
    print(f"--- Analyse du Texte ---\n")
    print(f"Texte : {doc.text}\n")
    print("--- Résultats des Correspondances ---")

    if matches:
        resultats = {}

        for match_id, start, end in matches:
            string_id = doc.vocab.strings[match_id]
            span = doc[start:end]

            if string_id not in resultats:
                resultats[string_id] = []

            # Enregistrer la forme textuelle trouvée
            resultats[string_id].append(span.text)

        # Afficher les mots-clés trouvés et leurs occurrences
        for mot, occurrences in resultats.items():
            print(f"✅ Mot-clé (Base Form) : **{mot}**")
            print(f"   Occurrences trouvées : {len(occurrences)}")
            # Afficher les formes exactes trouvées dans le texte
            print(f"   Formes exactes trouvées : {', '.join(occurrences)}")
    else:
        print("❌ Aucun des mots-clés n'a été trouvé dans le texte.")


mots_cles = ["google"]

# --- Configuration ---
# 1. Le texte à analyser
with open('map_descriptions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

@dataclass
class Metriques:
    TP: int = 0
    TN: int = 0
    FP: int = 0
    FN: int = 0
    precision: float = 0.0
    recall: float = 0.0

output =defaultdict(Metriques)
total_occurrences = 0
for map_description in data:
    print(f"Analyzing map: {map_description['map_name']} (Model: {map_description['model']})")
    text = map_description['map_description']
    matches, doc = analyze_text(text)
    #display_results(matches, doc, mots_cles)

    # Enregistrer les résultats dans le dictionnaire de sortie
    occurrences_count = len(matches)
    total_occurrences += occurrences_count

    # vérifie si c'est un vrai positif, faux positif, vrai négatif ou faux négatif
    if occurrences_count > 0 and "google" in map_description['map_name']:
        output[map_description['model']].TP += 1
    elif occurrences_count > 0 and "google" not in map_description['map_name']:
        output[map_description['model']].FP += 1
    elif occurrences_count == 0 and "google" in map_description['map_name']:
        output[map_description['model']].FN += 1
    else:
        output[map_description['model']].TN += 1

print(f"Total occurrences of 'Google': {total_occurrences}")
# compute precision and recall for each model
for model, metriques in output.items():
    metriques.precision = metriques.TP / (metriques.TP + metriques.FP) if (metriques.TP + metriques.FP) > 0 else 0
    metriques.recall = metriques.TP / (metriques.TP + metriques.FN) if (metriques.TP + metriques.FN) > 0 else 0
    print(f"Model: {model}, Precision: {metriques.precision:.2f}, Recall: {metriques.recall:.2f}")
    

