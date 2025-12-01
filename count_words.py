import spacy
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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

with open('map_descriptions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
nlp = spacy.load("en_core_web_md")

output = {}
output["word_count"] = []
output["sent_count"] = []
output["map_name"] = []
output["model"] = []

for map_description in data:
    text = map_description['map_description']
    doc = nlp(text)
    word_count = count_words_in_text(doc)
    sent_count = count_sentences_in_text(doc)

    output["word_count"].append(word_count)
    output["sent_count"].append(sent_count)
    output["map_name"].append(map_description['map_name'])
    output["model"].append(map_description['model'])

plot_sentences_map(output)