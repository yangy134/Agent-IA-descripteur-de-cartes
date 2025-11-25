# Map descriptions vlm scripts

Python scripts to collect and analyze the map descriptions from VLM

## Markdown descriptions hierarchy

`descriptions` folder contains all markdown files for the maps descriptions. Each folder represents a language model, and each file inside is named after the map it describes and the zoom level (i.e. `osm_18` for OSM map and zoom level 18).

All markdown files follow the same structure:

```markdown
# Can you describe the content of this map?

Map general description.

# Can you describe the most visually salient elements of the map?

Map most visually salient elements description.

# Anchors summary

Map anchors summary description. 
```

The anchors summary is a simple markdown list of anchors extracted from the second part of the description. It was generated with GPT-5 Mini using `generate_anchors_summary.py`.

The file will only contain the text `Erreur` in case the model was not able to generate a description.
