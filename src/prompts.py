# src/prompts.py
# ------------------------------------------------------------
# Prompt templates used by the C1 pipeline.
# Adjust these strings to fine‑tune the behavior of each LLM.
# ------------------------------------------------------------

# 1️⃣ Prompt for the spatial model (Qwen‑VL). It receives the path
#    (or a description) of the image and should return a concise
#    structured description of the geographic elements present.
SPATIAL_PROMPT = (
    "You are given a map image located at {image_path}. "
    "Extract and list all major geographic features, streets, "
    "landmarks, and any textual annotations. Return a JSON‑like "
    "structure with keys: 'roads', 'landmarks', 'labels', 'coordinates'."
)

# 2️⃣ Prompt for the voirie model (Gemma). It receives the raw
#    spatial output and should interpret it in a way that is useful "
#    "for accessibility (e.g., simplify street names, indicate "
#    "crossings, describe obstacles).""
VERIE_PROMPT = (
    "You are an expert in urban planning and accessibility. "
    "Based on the following spatial extraction, produce a clear "
    "textual description that a visually‑impaired person can understand. "
    "Focus on navigation cues, important landmarks, and any "
    "potential hazards. Output plain French sentences.\n\n"
    "Spatial output:\n{spatial_output}"
)

# 3️⃣ Prompt for the synthesis model (Llama). It receives the
#    processed description and must generate a final, fluid, "
#    "accessible description that can be spoken aloud."
SYNTHESIS_PROMPT = (
    "You are a friendly assistant that creates an accessible description "
    "of a city centre for a blind user. Using the following detailed "
    "information, write a concise, natural‑language paragraph in French. "
    "Make it easy to follow, mention key streets, landmarks, and directions.\n\n"
    "Processed description:\n{verie_output}"
)
