import spacy
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_toponyms_map(dict):
    dict_df = pd.DataFrame.from_dict(dict)
    counts = {"chatgpt": [], "human": [], "gemini": [], "claude": [], 
                  "llama-3.2-11b-vision-instruct": [], "gemma-3-12b": [], "gemma-3-4b": [],
                "qwen2.5-vl-7b": [], "deepseek": [], "le_chat": []}
    for i, row in dict_df.iterrows():
        word_count = row['toponym_count']
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
    ax.set_ylabel('toponym count')
    bplot = ax.boxplot(array_occurrences,
                    tick_labels=labels)  # will be used to label x-ticks

    # Force y-axis to display decimal values instead of rounding to integers
    ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=10, integer=False))

    # Calculate and plot the mean for each distribution
    means = [np.mean(data) for data in array_occurrences]
    ax.scatter(range(1, len(means) + 1), means, color='red', marker='D', s=50, zorder=3, label='Mean')
    ax.legend()

    plt.show()

nlp = spacy.load('en_core_web_md')

with open('map_descriptions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

output = {}
output["toponym_count"] = []
output["toponyms"] = []
output["NER"] = []
output["map_name"] = []
output["model"] = []

for map_description in data:
    text = map_description['map_description']
    doc = nlp(text)
    toponym_count = 0
    toponyms = []
    ner = []
    for ent in doc.ents:
        ner.append((ent.text, ent.label_))
        if ent.label_ in ['GPE', 'LOC', 'FAC']:
            toponym_count += 1
            toponyms.append(ent.text)  

    output["toponym_count"].append(toponym_count)
    output["toponyms"].append(toponyms)
    output["NER"].append(ner)
    output["map_name"].append(map_description['map_name'])
    output["model"].append(map_description['model'])

plot_toponyms_map(output)
print(output["NER"][3])