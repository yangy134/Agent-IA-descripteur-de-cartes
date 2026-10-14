import csv
import re
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path
import re

def display_output(output):
    data = []
    for i in range(len(output["model"])):
        model = output["model"][i]
        if model == "chatgpt":
            model = "ChatGPT"
        elif model == "gemini":
            model = "Gemini"
        elif model == "claude":
            model = "Claude"
        elif model == "llama-3.2-11b-vision-instruct":
            model = "Llama"
        elif model == "qwen2.5-vl-7b":
            model = "Qwen"
        elif model == "gemma-3-12b":
            model = "Gemma-12b"
        elif model == "gemma-3-4b":
            model = "Gemma-4b"
        elif model == "le_chat":
            model = "Le Chat"
        elif model == "deepseek":
            model = "DeepSeek"
        toponyms = output["toponyms"][i]
        spatial_relations = output["spatial relations"][i]
        data.append({"Model": model, "Map": output["map_name"][i], "Annotation": "toponyms", "Count": len(toponyms)})
        data.append({"Model": model, "Map": output["map_name"][i], "Annotation": "spatial relations", "Count": len(spatial_relations)})

    df = pd.DataFrame(data)
    print(df)

    # Box plots groupés
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=df, x="Model", y="Count", hue="Annotation")
    plt.title("Comparaison des distributions par catégorie")
    plt.show()

    # Violin plots
    plt.figure(figsize=(12, 6))
    sns.violinplot(data=df, x="Model", y="Count", hue="Annotation", split=True)
    plt.title("Densité des distributions par catégorie")
    plt.show()


def read_tsv_file(file, model, map_name):
    output_dict = {}
    output_dict["toponyms"] = []
    output_dict["spatial relations"] = []
    output_dict["map_name"] = []
    output_dict["model"] = []

    with open(file, newline='', encoding="utf8") as file:
        tsv_reader = csv.reader(file, delimiter='\t')
        toponyms = []
        spatial_relations = []
        dict_id_text = {}
        dict_id_type = {}
        for row in tsv_reader:
            if len(row) == 7:
                if len(row[5]) < 3:
                    continue
                match = re.search(r'\[(.*?)\]', row[5])
                id = -1
                if match:
                    id = int(match.group(1))
                type = row[5]
                start = type.find('[')
                if start != -1:
                    type = type[:start].strip()
                if id == -1:
                    if type == "toponym":
                        toponyms.append(row[2])
                    elif type == "spatial relation":
                        spatial_relations.append(row[2])
                else:
                    if id in list(dict_id_text.keys()):
                        text = dict_id_text[id]
                        text += " " + row[2]
                        dict_id_text[id] = text
                    else:
                        dict_id_text[id] = row[2]
                        dict_id_type[id] = type
            
        for id in dict_id_text.keys():
            if dict_id_type[id] == "toponym":
                toponyms.append(dict_id_text[id])
            elif dict_id_type[id] == "spatial relation":
                spatial_relations.append(dict_id_text[id])
        # get the parent directory name to get the model and map name
        output_dict["model"].append(model)
        output_dict["map_name"].append(map_name)
        output_dict["toponyms"].append(toponyms)
        output_dict["spatial relations"].append(spatial_relations)

    return output_dict

def process_annotations():

    output = {}
    output["toponyms"] = []
    output["spatial relations"] = []
    output["map_name"] = []
    output["model"] = []

    for filepath in Path("annotations/annotation").rglob('*.tsv'):
        if filepath.is_file():
            if re.search(r"INITIAL", filepath.name):
                continue
            with open(filepath, newline='', encoding="utf8") as file:
                tsv_reader = csv.reader(file, delimiter='\t')
                toponyms = []
                spatial_relations = []
                dict_id_text = {}
                dict_id_type = {}
                for row in tsv_reader:
                    if len(row) == 7:
                        if len(row[5]) < 3:
                            continue
                        match = re.search(r'\[(.*?)\]', row[5])
                        id = -1
                        if match:
                            id = int(match.group(1))
                        type = row[5]
                        start = type.find('[')
                        if start != -1:
                            type = type[:start].strip()
                        if id == -1:
                            if type == "toponym":
                                toponyms.append(row[2])
                            elif type == "spatial relation":
                                spatial_relations.append(row[2])
                        else:
                            if id in list(dict_id_text.keys()):
                                text = dict_id_text[id]
                                text += " " + row[2]
                                dict_id_text[id] = text
                            else:
                                dict_id_text[id] = row[2]
                                dict_id_type[id] = type
                
                for id in dict_id_text.keys():
                    if dict_id_type[id] == "toponym":
                        toponyms.append(dict_id_text[id])
                    elif dict_id_type[id] == "spatial relation":
                        spatial_relations.append(dict_id_text[id])
                # get the parent directory name to get the model and map name
                dir_name = filepath.parent.name
                output["model"].append(dir_name.split("_")[0])
                output["map_name"].append(dir_name.split("_")[1])
                output["toponyms"].append(toponyms)
                output["spatial relations"].append(spatial_relations)
    return output

output = process_annotations()
counts = {}
for item in output["model"]:
    counts[item] = counts.get(item, 0) + 1
print(counts)

#print(len(output["map_name"]))
#print(output["toponyms"][len(output["toponyms"])-1])
#output_qwen =read_tsv_file("annotations/annotation/qwen2.5-7b_rotated_18.html/admin.tsv", "qwen2.5-vl-7b", "rotated_18")
#print(output_qwen)
display_output(output)