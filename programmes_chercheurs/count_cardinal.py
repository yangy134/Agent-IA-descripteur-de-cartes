import spacy
from spacy.matcher import Matcher
import json
import pandas as pd
import math
import matplotlib.pyplot as plt
import numpy as np
import scikit_posthocs as sp
from scipy import stats


## Analyse le texte pour trouver la présence de mots clés et leur nombre
def analyze_text(text, keywords):
    # Charger le modèle linguistique SpaCy
    nlp = spacy.load("en_core_web_md")

    # Créer un objet Matcher
    matcher = Matcher(nlp.vocab)

    # Utilisation de l'attribut LEMMA
    for mot in keywords:
        pattern = [{"LEMMA": mot.lower()}]
        matcher.add(mot, [pattern])

    # Traiter le texte avec SpaCy (cette étape calcule les lemmes !)
    doc = nlp(text)

    # Appliquer le Matcher au Doc pour trouver les correspondances
    matches = matcher(doc)

    return matches, doc

def display_results(matches, doc, keywords):
    print(f"--- Analyse du Texte ---\n")
    print(f"Texte : {doc.text}\n")
    print(f"Mots-clés recherchés (formes de base) : {keywords}\n")
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


## Créé le graphique d'occurence des mots
def plot_occurences_map(dict):
    dict_df = pd.DataFrame.from_dict(dict)
    occurences = {"chatgpt": [], "human": [], "gemini": [], "claude": [], 
                  "llama-3.2-11b-vision-instruct": [], "gemma-3-12b": [], "gemma-3-4b": [],
                "qwen2.5-vl-7b": [], "deepseek": [], "le_chat": []}
    for i, row in dict_df.iterrows():
        occurences_in_model = row['occurrences']
        model = row['model']
        occurences[model].append(occurences_in_model)

    array_occurrences = []
    labels = []

    for key, array in occurences.items():
        name = key
        if(name == "gemma-3-4b"):
            name = "gemma-4b"
        if(name == "gemma-3-12b"):
            name = "gemma-12b"
        if(name == "llama-3.2-11b-vision-instruct"):
            name = "Llama"
        if(name == "qwen2.5-vl-7b"):
            name = "Qwen"
        labels.append(name)
        array_occurrences.append(array)

    #print(stats.describe(array_localisation))

    fig, ax = plt.subplots()
    ax.set_ylabel('keyword occurrences')

    bplot = ax.boxplot(array_occurrences,
                    tick_labels=labels)  # will be used to label x-ticks

    # Force y-axis to display decimal values instead of rounding to integers
    ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=10, integer=False))

    # Calculate and plot the mean for each distribution
    means = [np.mean(data) for data in array_occurrences]
    ax.scatter(range(1, len(means) + 1), means, color='red', marker='D', s=50, zorder=3, label='Mean')
    ax.legend()

    plt.show()

def plot_diversity_map(dict):
    dict_df = pd.DataFrame.from_dict(dict)
    occurences = {"chatgpt": [], "human": [], "gemini": [], "claude": [], 
                  "llama-3.2-11b-vision-instruct": [], "gemma-3-12b": [], "gemma-3-4b": [],
                "qwen2.5-vl-7b": [], "deepseek": [], "le_chat": []}
    for i, row in dict_df.iterrows():
        occurences_in_model = row['diversity']
        model = row['model']
        occurences[model].append(occurences_in_model)

    array_occurrences = []
    labels = []

    for key, array in occurences.items():
        name = key
        if(name == "gemma-3-4b"):
            name = "gemma-4b"
        if(name == "gemma-3-12b"):
            name = "gemma-12b"
        if(name == "llama-3.2-11b-vision-instruct"):
            name = "Llama"
        if(name == "qwen2.5-vl-7b"):
            name = "Qwen"
        labels.append(name)
        array_occurrences.append(array)

    #print(stats.describe(array_localisation))

    fig, ax = plt.subplots()
    ax.set_ylabel('keyword diversity')

    bplot = ax.boxplot(array_occurrences,
                    tick_labels=labels)  # will be used to label x-ticks

    # Force y-axis to display decimal values instead of rounding to integers
    ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=10, integer=False))

    # Calculate and plot the mean for each distribution
    means = [np.mean(data) for data in array_occurrences]
    ax.scatter(range(1, len(means) + 1), means, color='red', marker='D', s=50, zorder=3, label='Mean')
    ax.legend()

    plt.show()

def plot_density_map(dict):
    dict_df = pd.DataFrame.from_dict(dict)
    occurences = {"chatgpt": [], "human": [], "gemini": [], "claude": [], 
                  "llama-3.2-11b-vision-instruct": [], "gemma-3-12b": [], "gemma-3-4b": [],
                "qwen2.5-vl-7b": [], "deepseek": [], "le_chat": []}
    for i, row in dict_df.iterrows():
        occurences_in_model = row['density']
        model = row['model']
        occurences[model].append(occurences_in_model)

    array_occurrences = []
    labels = []

    for key, array in occurences.items():
        name = key
        if(name == "gemma-3-4b"):
            name = "gemma-4b"
        if(name == "gemma-3-12b"):
            name = "gemma-12b"
        if(name == "llama-3.2-11b-vision-instruct"):
            name = "Llama"
        if(name == "qwen2.5-vl-7b"):
            name = "Qwen"
        labels.append(name)
        array_occurrences.append(array)

    #print(stats.describe(array_localisation))

    fig, ax = plt.subplots()
    ax.set_ylabel('keyword density')

    bplot = ax.boxplot(array_occurrences,
                    tick_labels=labels)  # will be used to label x-ticks

    # Force y-axis to display decimal values instead of rounding to integers
    ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=10, integer=False))

    # Calculate and plot the mean for each distribution
    means = [np.mean(data) for data in array_occurrences]
    ax.scatter(range(1, len(means) + 1), means, color='red', marker='D', s=50, zorder=3, label='Mean')
    ax.legend()

    plt.show()

# --- Configuration ---
# 1. Le texte à analyser
with open('map_descriptions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

output = {}
output["occurrences"] = []
output["diversity"] = []
output["map_name"] = []
output["model"] = []
output["density"] = []

# 2. La liste des mots-clés à rechercher
# Les mots-clés sont sensibles à la casse par défaut.
mots_cles = ["east", "west", "north", "south", "southwest", "southeast", "northwest", "northeast"]

count_rotated_18 = 0
matches_rotated_18 = 0
count_non_rotated_18 = 0
matches_non_rotated_18 = 0
for map_description in data:
    if map_description['map_name'] == "rotated_18":
        text = map_description['map_description']
        matches, doc = analyze_text(text, mots_cles)
        
        matches_rotated_18 += len(matches)
        if len(matches) > 0:
            count_rotated_18 += 1
            print(f"Map: {map_description['map_name']}, Model: {map_description['model']}")

    else:
        text = map_description['map_description']
        matches, doc = analyze_text(text, mots_cles)
        
        matches_non_rotated_18 += len(matches)
        if len(matches) > 0:
            count_non_rotated_18 += 1

print(f"Rotated 18 : {matches_rotated_18} matches, {count_rotated_18} maps with matches")
print(f"Non-rotated 18 : {matches_non_rotated_18} matches, {count_non_rotated_18} maps with matches")