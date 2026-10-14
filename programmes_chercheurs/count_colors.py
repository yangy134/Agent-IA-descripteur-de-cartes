import spacy
from spacy.matcher import Matcher
import json
import pandas as pd
import math
import matplotlib.pyplot as plt
import numpy as np
import scikit_posthocs as sp
from scipy import stats

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
    ax.set_ylabel('color occurrences')

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
    ax.set_ylabel('color diversity')

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
mots_cles = ["blue", "red", "green", "yellow", "black", "white", "orange", "purple",
             "pink", "brown", "gray", "grey", "cyan", "magenta", "beige", "maroon", "navy",
             "turquoise", "lavender", "gold", "silver", "bronze", "teal", "olive", "peach", 
             "lime", "indigo", "aqua", "coral", "ivory", "khaki", "plum", "salmon", "tan", 
             "violet", "amber", "burgundy", "cerulean", "charcoal", "crimson", "fuchsia", 
             "jade", "mustard", "ochre", "saffron", "sepia", "sienna", "vermilion", "shade", 
             "hue", "tint", "tone", "saturation", "brightness", "contrast", "palette", 
             "spectrum", "gradient", "monochrome", "pastel", "color", "colour", "icon", 
             "symbol", "marker", "dark", "light", "label", "line", "border", "fill", 
             "shading", "dashed", "dotted", "scale", "legend", "contour"]

for map_description in data:
    text = map_description['map_description']
    matches, doc = analyze_text(text, mots_cles)
    #display_results(matches, doc, mots_cles)
    word_count = len([token for token in doc if not token.is_punct and not token.is_space])

    # Enregistrer les résultats dans le dictionnaire de sortie
    occurrences_count = len(matches)
    diversity_count = len(set([doc.vocab.strings[match_id] for match_id, start, end in matches]))

    output["occurrences"].append(occurrences_count)
    output["diversity"].append(diversity_count)
    output["map_name"].append(map_description['map_name'])
    output["model"].append(map_description['model'])
    output["density"].append(occurrences_count / word_count if word_count > 0 else 0)

plot_occurences_map(output)
plot_diversity_map(output)
plot_density_map(output)
# Test de Kruskal-Wallis
df = pd.DataFrame(output)
df_gpt = df[df['model'] == 'chatgpt']
df_gemini = df[df['model'] == 'gemini']
df_claude = df[df['model'] == 'claude']
df_mistral = df[df['model'] == 'le_chat']
df_llama = df[df['model'] == 'llama-3.2-11b-vision-instruct']
df_gemma_12b = df[df['model'] == 'gemma-3-12b']
df_gemma_4b = df[df['model'] == 'gemma-3-4b']
df_qwen = df[df['model'] == 'qwen2.5-vl-7b']
df_deepseek = df[df['model'] == 'deepseek']

stat_, p_value = stats.kruskal(df_gpt['density'], df_gemini['density'], df_claude['density'], df_mistral['density'], df_llama['density'], df_gemma_12b['density'], df_gemma_4b['density'], df_qwen['density'], df_deepseek['density'])
print(f"Test de Kruskal-Wallis sur la moyenne du score : {stat_:.3f} (p-value: {p_value:.4e})")
posthoc = sp.posthoc_dunn(df, val_col='density', group_col='model', p_adjust='bonferroni')
print(posthoc)