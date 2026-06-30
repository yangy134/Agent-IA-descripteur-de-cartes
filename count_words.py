import spacy
from spacy.matcher import Matcher
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import seaborn as sns
from scipy import stats
import scikit_posthocs as sp

def count_words_in_text(doc):
    word_count = len([token for token in doc if not token.is_punct and not token.is_space])

    return word_count

def count_sentences_in_text(doc):
    sentence_count = len(list(doc.sents))
    return sentence_count

def plot_words_map(dict):
    dict_df = pd.DataFrame.from_dict(dict)
    counts = {"chatgpt": [], "human": [], "gemini": [], "claude": [], 
                  "llama-3.2-11b-vision-instruct": [], "gemma-3-12b": [], "gemma-3-4b": [],
                "qwen2.5-vl-7b": [], "deepseek": [], "le_chat": []}
    for i, row in dict_df.iterrows():
        word_count = row['word_count']
        model = row['model']
        counts[model].append(word_count)

    array_occurrences = []
    labels = []

    for key, array in counts.items():
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
    ax.set_ylabel('word count')
    bplot = ax.boxplot(array_occurrences,
                    tick_labels=labels)  # will be used to label x-ticks

    # Force y-axis to display decimal values instead of rounding to integers
    ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=10, integer=False))

    # Calculate and plot the mean for each distribution
    means = [np.mean(data) for data in array_occurrences]
    ax.scatter(range(1, len(means) + 1), means, color='red', marker='D', s=50, zorder=3, label='Mean')
    ax.legend()

    plt.show()


def plot_sentences_map(dict):
    dict_df = pd.DataFrame.from_dict(dict)
    counts = {"chatgpt": [], "human": [], "gemini": [], "claude": [], 
                  "llama-3.2-11b-vision-instruct": [], "gemma-3-12b": [], "gemma-3-4b": [],
                "qwen2.5-vl-7b": [], "deepseek": [], "le_chat": []}
    for i, row in dict_df.iterrows():
        word_count = row['sent_count']
        model = row['model']
        counts[model].append(word_count)

    array_occurrences = []
    labels = []

    for key, array in counts.items():
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
    ax.set_ylabel('sentence count')
    bplot = ax.boxplot(array_occurrences,
                    tick_labels=labels)  # will be used to label x-ticks

    # Force y-axis to display decimal values instead of rounding to integers
    ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=10, integer=False))

    # Calculate and plot the mean for each distribution
    means = [np.mean(data) for data in array_occurrences]
    ax.scatter(range(1, len(means) + 1), means, color='red', marker='D', s=50, zorder=3, label='Mean')
    ax.legend()

    plt.show()

def plot_words_sentences_zoom(output, max_word_count, max_sentence_count, max_geo_keyword, max_carto_keyword):
    data = []
    for i in range(len(output["model"])):
        name = output["model"][i]
        map_name = output["map_name"][i]
        word_count = output["word_count"][i] / max_word_count
        sent_count = output["sentence_count"][i] / max_sentence_count
        carto_keyword = output["occurrences_color"][i] / max_carto_keyword if max_carto_keyword > 0 else 0
        geo_keyword = output["occurrences_geo"][i] / max_geo_keyword if max_geo_keyword > 0 else 0
        
        if "google" in map_name.lower():
            map_group = "Google Maps"
        elif "openstreet" in map_name.lower():
            map_group = "OpenStreetMap"
        elif "ign" in map_name.lower():
            map_group = "IGN"
        else:
            map_group = "Others"
        
        if "12" in map_name.lower():
            scale_group = "12"
        elif "14" in map_name.lower():
            scale_group = "14"
        elif "16" in map_name.lower():
            scale_group = "16"
        elif "18" in map_name.lower():
            scale_group = "18"
        data.append({"Model": name, "Map": map_name, "Metric": "word_count", "Count": word_count, "Map_group": map_group, "Scale_group": scale_group})
        data.append({"Model": name, "Map": map_name, "Metric": "sentence_count", "Count": sent_count, "Map_group": map_group, "Scale_group": scale_group})
        data.append({"Model": name, "Map": map_name, "Metric": "geo_keyword", "Count": geo_keyword, "Map_group": map_group, "Scale_group": scale_group})
        data.append({"Model": name, "Map": map_name, "Metric": "carto_keyword", "Count": carto_keyword, "Map_group": map_group, "Scale_group": scale_group})

    df = pd.DataFrame(data)

    df_filtered = df[df['Metric'].isin(["word_count", "sentence_count","geo_keyword","carto_keyword"])]
    
    df_12 = df[(df['Scale_group'] == '12') & (df['Metric'] == 'word_count')]
    df_14 = df[(df['Scale_group'] == '14') & (df['Metric'] == 'word_count')]
    df_16 = df[(df['Scale_group'] == '16') & (df['Metric'] == 'word_count')]
    df_18 = df[(df['Scale_group'] == '18') & (df['Metric'] == 'word_count')]
    stat_w, p_value_w = stats.kruskal(df_12['Count'], df_14['Count'], df_16['Count'], df_18['Count'])
    print(f"Test de Kruskal-Wallis sur la moyenne du score (word_count) : {stat_w:.3f} (p-value: {p_value_w:.4e})")
    
    df_12 = df[(df['Scale_group'] == '12') & (df['Metric'] == 'sentence_count')]
    df_14 = df[(df['Scale_group'] == '14') & (df['Metric'] == 'sentence_count')]
    df_16 = df[(df['Scale_group'] == '16') & (df['Metric'] == 'sentence_count')]
    df_18 = df[(df['Scale_group'] == '18') & (df['Metric'] == 'sentence_count')]
    stat_s, p_value_s = stats.kruskal(df_12['Count'], df_14['Count'], df_16['Count'], df_18['Count'])
    print(f"Test de Kruskal-Wallis sur la moyenne du score (sentence_count) : {stat_s:.3f} (p-value: {p_value_s:.4e})")
    
    df_12 = df[(df['Scale_group'] == '12') & (df['Metric'] == 'geo_keyword')]
    df_14 = df[(df['Scale_group'] == '14') & (df['Metric'] == 'geo_keyword')]
    df_16 = df[(df['Scale_group'] == '16') & (df['Metric'] == 'geo_keyword')]
    df_18 = df[(df['Scale_group'] == '18') & (df['Metric'] == 'geo_keyword')]
    stat_g, p_value_g = stats.kruskal(df_12['Count'], df_14['Count'], df_16['Count'], df_18['Count'])
    print(f"Test de Kruskal-Wallis sur la moyenne du score (geo_keyword) : {stat_g:.3f} (p-value: {p_value_g:.4e})")
    posthoc = sp.posthoc_dunn(df[df['Metric'] == 'geo_keyword'], val_col='Count', group_col='Scale_group', p_adjust='bonferroni')
    print(posthoc)

    df_12 = df[(df['Scale_group'] == '12') & (df['Metric'] == 'carto_keyword')]
    df_14 = df[(df['Scale_group'] == '14') & (df['Metric'] == 'carto_keyword')]
    df_16 = df[(df['Scale_group'] == '16') & (df['Metric'] == 'carto_keyword')]
    df_18 = df[(df['Scale_group'] == '18') & (df['Metric'] == 'carto_keyword')]
    stat_c, p_value_c = stats.kruskal(df_12['Count'], df_14['Count'], df_16['Count'], df_18['Count'])
    print(f"Test de Kruskal-Wallis sur la moyenne du score (carto_keyword) : {stat_c:.3f} (p-value: {p_value_c:.4e})")

    plt.figure(figsize=(14, 6))
    sns.boxplot(x='Scale_group', y='Count', hue='Metric', data=df_filtered)
    #plt.title('Boxplot of the Error Types by Map Group')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

with open('map_descriptions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
nlp = spacy.load("en_core_web_md")

mots_cles_geo = ["river", "forest", "building", "sea", "lake", "mountain", "road", "bridge", 
             "street", "park", "hill", "valley", "island", "coast", "ocean", "cemetery", 
             "school", "hospital", "airport", "station", "harbor", "church", "stadium",
             "highway", "wood", "swamp", "desert", "stream", "dam", "railroad", "parking",
             "neighborhood", "bus stop", "zoo", "garden", "playground", "theater", "mall",
             "market", "settlement", "village", "town", "city", "capital", "province", "country",
             "continent", "glacier", "volcano", "bay", "gulf", "railway", "canal", "pier", 
             "lighthouse", "isthmus", "plateau", "prairie", "reef", "lagoon", "waterway",
             "tributary", "roundabout", "crossroad", "alley", "cul-de-sac", "facility", 
             "site", "plaza", "avenue", "boulevard", "drive", "court", "terrace", 
             "esplanade", "marsh", "estuary", "riverbank", "inlet", "dock", "quay"]
matcher_geo = Matcher(nlp.vocab)
for mot in mots_cles_geo:
    pattern = [{"LEMMA": mot.lower()}]
    matcher_geo.add(mot, [pattern])

mots_cles_color = ["blue", "red", "green", "yellow", "black", "white", "orange", "purple",
             "pink", "brown", "gray", "grey", "cyan", "magenta", "beige", "maroon", "navy",
             "turquoise", "lavender", "gold", "silver", "bronze", "teal", "olive", "peach", 
             "lime", "indigo", "aqua", "coral", "ivory", "khaki", "plum", "salmon", "tan", 
             "violet", "amber", "burgundy", "cerulean", "charcoal", "crimson", "fuchsia", 
             "jade", "mustard", "ochre", "saffron", "sepia", "sienna", "vermilion", "shade", 
             "hue", "tint", "tone", "saturation", "brightness", "contrast", "palette", 
             "spectrum", "gradient", "monochrome", "pastel", "color", "colour", "icon", 
             "symbol", "marker", "dark", "light", "label", "line", "border", "fill", 
             "shading", "dashed", "dotted", "scale", "legend", "contour"]
matcher_color = Matcher(nlp.vocab)
for mot in mots_cles_color:
    pattern = [{"LEMMA": mot.lower()}]
    matcher_color.add(mot, [pattern])

output = {}
output["word_count"] = []
output["sentence_count"] = []
output["map_name"] = []
output["model"] = []
output["occurrences_geo"] = []
output["occurrences_color"] = []

max_word_count = 0
max_sentence_count = 0
max_geo_keyword = 0
max_carto_keyword = 0
for map_description in data:
    text = map_description['map_description']
    doc = nlp(text)
    word_count = count_words_in_text(doc)
    sent_count = count_sentences_in_text(doc)
    matches_geo = len(matcher_geo(doc)) / word_count if word_count > 0 else 0
    matches_color = len(matcher_color(doc)) / word_count if word_count > 0 else 0

    if word_count > max_word_count:
        max_word_count = word_count
    if sent_count > max_sentence_count:
        max_sentence_count = sent_count
    if matches_geo > max_geo_keyword:
        max_geo_keyword = matches_geo
    if matches_color > max_carto_keyword:
        max_carto_keyword = matches_color

    output["word_count"].append(word_count)
    output["sentence_count"].append(sent_count)
    output["occurrences_geo"].append(matches_geo)
    output["occurrences_color"].append(matches_color)
    output["map_name"].append(map_description['map_name'])
    output["model"].append(map_description['model'])

#plot_words_map(output)

plot_words_sentences_zoom(output, max_word_count, max_sentence_count, max_geo_keyword, max_carto_keyword)