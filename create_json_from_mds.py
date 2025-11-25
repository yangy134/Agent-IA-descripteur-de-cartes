import os
import json

def find_markdown_files(root):
    for folder, _, files in os.walk(root):
        for file in files:
            if file.lower().endswith(".md"):
                if file != "README.md":
                    yield os.path.join(folder, file)

maps = []
for md in find_markdown_files("./"):

    # Get description informations from filename
    model = md.split('/')[2]
    map_name = md.split('/')[3].split('.')[0]
    scale = md.split('/')[3].split('.')[0].split('_')[-1]

    with open(md, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # If first line contains "Erreur", skip the file
    if lines[0].startswith("Erreur"):
        continue

    description = {
        "map_content": [],
        "salient_elements": [],
        "anchors_summary": []
    }
    current_part = "map_content"
    skip_next_line = False
    for line in lines:
        if skip_next_line:
            skip_next_line = False
            continue
        if line.startswith("# Can you describe the content of this map?"):
            skip_next_line = True
            continue
        if line.startswith("# Can you describe the most visually salient elements of the map?"):
            current_part = "salient_elements"
            skip_next_line = True
            continue
        if line.startswith("# Anchors summary"):
            current_part = "anchors_summary"
            skip_next_line = True
            continue
        description[current_part].append(line)

    map_content = "".join(description["map_content"]).strip()
    salient_elements = "".join(description["salient_elements"]).strip()
    anchors_summary = "".join(description["anchors_summary"]).strip()

    anchors = []
    for line in anchors_summary.split('\n'):
        if line.startswith("-"):
            anchors.append(line[2:].strip())

    maps.append({
        "map_name": map_name,
        "scale": scale,
        "model": model,
        "map_description": map_content,
        "anchors_description": salient_elements,
        "anchors": anchors
    })

json.dump(maps, open("map_descriptions.json", "w"), indent=4)
