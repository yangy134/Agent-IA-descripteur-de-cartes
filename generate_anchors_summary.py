import os

from openai import OpenAI

API_KEY = os.environ['OPENAI_API_KEY']
MODEL = "gpt-5-mini"

client = OpenAI(api_key=API_KEY)


def find_markdown_files(root):
    for folder, _, files in os.walk(root):
        for file in files:
            if file.lower().endswith(".md"):
                if file != "README.md":
                    yield os.path.join(folder, file)


for md in find_markdown_files("./"):

    print(md)

    with open(md, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # If first line contains "Erreur", skip the file
    if lines[0].startswith("Erreur"):
        continue

    # Ask the model to extract a markdown list of landmarks
    text = "".join(lines)
    prompt = (
        "Extract a markdown list (not numbered) with identified landmarks under "
        '"# Can you describe the most visually salient elements of the map?". '
        "Identify also non-named landmarks cited. Give me just the list."
    )
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": f"{prompt}\n\n{text}"}],
    )
    anchors = completion.choices[0].message.content

    with open(md, "a", encoding="utf-8") as f:
        f.write("\n# Anchors summary\n\n")
        f.write(anchors.strip() + "\n")
