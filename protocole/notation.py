"""
Notation des descriptions de cartes produites par l'agent, par rapport à la vérité terrain (VT).

Entrées
-------
- sortie.txt : descriptions générées, une section par carte, introduite par une ligne
  du type ``—-----campus_z15_google`` (scène + niveau de zoom + service carto).
- VT.csv     : vérité terrain. Colonnes :
  scene, id, categorie, nom, zones, importance, visible_google, visible_apple, visible_osm
  Valeurs de visibilité : N = nommé sur la carte, T = tracé visible sans nom, 0 = absent.

Principe
--------
Pour chaque section (scène, zoom, service), on ne retient que les lignes de VT de la
même scène (même zoom) et on lit la colonne de visibilité du service concerné.

1. Rappel pondéré : part des éléments visibles (N ou T) retrouvés dans la description,
   pondérée par l'importance (1 = essentiel ... 5 = détail ;
   poids 1 -> 1.0, 2 -> 0.8, 3 -> 0.6, 4 -> 0.4, 5 -> 0.2).
   - éléments nommés  : appariement du nom (tokens spaCy, normalisation, tolérance aux fautes) ;
   - éléments anonymes ou seulement tracés (T) : mention générique (rivière, route, étang…)
     dans la bonne zone ;
   - cadrage (zones = "toutes") : recouvrement des lemmes avec le texte.
2. Localisation : pour les éléments nommés retrouvés, la position cardinale citée est
   comparée aux zones de la VT (1 = même zone, 0.5 = zone voisine, 0 = faux).
3. Précision : part des éléments nommés cités (sections AXES et REPÈRES) qui existent
   dans la VT pour ce service. Un élément de la VT absent du service (0) compte 0.5
   (connaissance extérieure à la carte), un élément inconnu compte 0.

Note /20 = 20 x (0.5 x rappel + 0.3 x précision + 0.2 x localisation).

Usage
-----
    python notation.py [sortie.txt] [VT.csv] [--detail] [--csv resultats.csv]
"""

from __future__ import annotations

import argparse
import csv
import difflib
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import spacy

# --------------------------------------------------------------------------- #
# Paramètres
# --------------------------------------------------------------------------- #

SERVICES = ("google", "apple", "osm")
IMPORTANCE_MIN, IMPORTANCE_MAX = 1, 5     # 1 = essentiel, 5 = détail
POIDS_IMPORTANCE = {1: 1, 2: 0.5, 3: 0.25, 4: 0.12, 5: 0.06}
IMPORTANCE_DEFAUT = 3
POIDS_NOTE = {"rappel": 0.5, "precision": 0.3, "localisation": 0.2}
SEUIL_NOM = 0.70          # similarité minimale pour apparier un nom
SEUIL_TOKEN = 0.85        # similarité minimale entre deux tokens (fautes de frappe)
SEUIL_VECTEUR = 0.70      # similarité vectorielle spaCy minimale entre deux mots
SEUIL_CADRAGE = 0.50      # recouvrement minimal pour un élément de cadrage

# Mots "génériques" : peu discriminants pour un nom propre (poids réduit)
GENERIQUES = {
    "rue", "avenue", "boulevard", "allee", "chemin", "route", "autoroute", "impasse",
    "place", "cours", "quai", "pont", "voie", "rond", "point", "carrefour",
    "bois", "foret", "parc", "jardin", "stade", "gymnase", "ecole", "lycee", "college",
    "universite", "etang", "lac", "riviere", "ruisseau", "ru", "plan", "eau", "canal",
    "lande", "zone", "rocade", "departementale", "nationale", "primaire",
    "nord", "sud", "est", "ouest", "centre",
}
POIDS_GENERIQUE = 0.3

# Familles de mots pour les éléments anonymes ou seulement tracés
FAMILLES = {
    "eau_courante": {"riviere", "ruisseau", "ru", "cours d'eau", "fleuve", "canal", "torrent"},
    "eau_stagnante": {"etang", "lac", "mare", "plan d'eau", "bassin", "reservoir"},
    "route": {"route", "chemin", "voie", "rue", "departementale", "axe", "voirie", "nationale",
              "autoroute", "rocade"},
    "carrefour": {"carrefour", "rond-point", "intersection", "croisement", "echangeur"},
    "foret": {"foret", "bois", "boise", "boisement", "forestier"},
}

# Synonymes utiles pour le cadrage
SYNONYMES = {
    "rural": {"campagne", "agricole", "champetre"},
    "hameau": {"lieu-dit", "lieux-dits", "ferme", "village"},
    "disperser": {"disperse", "epars", "eparpille", "isole"},
    "bourg": {"centre-bourg", "village"},
    "mosaique": {"alternance", "patchwork", "melange"},
    "champ": {"parcelle", "agricole", "culture"},
    "ruisseau": {"riviere", "cours d'eau", "ru"},
    "campus": {"universite", "universitaire", "etudiant"},
    "universitaire": {"universite", "campus", "etudiant", "ecole", "enseignement"},
}

ABREVIATIONS = [
    (r"\bav\b\.?", "avenue"), (r"\bbd\b\.?", "boulevard"), (r"\ball\b\.?", "allee"),
    (r"\bch\b\.?", "chemin"), (r"\brte\b\.?", "route"), (r"\bpl\b\.?", "place"),
    (r"\bst\b", "saint"), (r"\bste\b", "sainte"), (r"\bimp\b\.?", "impasse"),
]

# Grille 3x3 des zones cardinales
GRILLE = {"NO": (0, 0), "N": (0, 1), "NE": (0, 2),
          "O": (1, 0), "C": (1, 1), "E": (1, 2),
          "SO": (2, 0), "S": (2, 1), "SE": (2, 2)}

SECTIONS = {"vue": "VUE D'ENSEMBLE", "axes": "AXES ET VOIRIE",
            "reperes": "REPÈRES REMARQUABLES", "incertitude": "POINTS D'INCERTITUDE"}


# --------------------------------------------------------------------------- #
# spaCy et normalisation
# --------------------------------------------------------------------------- #

def charger_spacy():
    for modele in ("fr_core_news_md", "fr_core_news_lg", "fr_core_news_sm"):
        try:
            return spacy.load(modele)
        except OSError:
            continue
    print("Aucun modèle français spaCy trouvé : python -m spacy download fr_core_news_md",
          file=sys.stderr)
    return spacy.blank("fr")


NLP = charger_spacy()
A_VECTEURS = NLP.vocab.vectors.shape[0] > 0


def sans_accents(texte: str) -> str:
    texte = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in texte if not unicodedata.combining(c))


def normaliser(texte: str) -> str:
    texte = sans_accents(texte.lower()).replace("’", "'").replace("`", "'")
    for motif, remplacement in ABREVIATIONS:
        texte = re.sub(motif, remplacement, texte)
    texte = re.sub(r"\b([adn])\s+(\d+)\b", r"\1\2", texte)   # "D 903" -> "d903"
    return re.sub(r"\s+", " ", texte).strip()


MOTS_VIDES = {normaliser(m) for m in NLP.Defaults.stop_words} | {"l", "d", "s", "n"}


@lru_cache(maxsize=None)
def doc(texte: str):
    return NLP(texte)


@lru_cache(maxsize=None)
def tokens_nom(texte: str) -> tuple[str, ...]:
    """Tokens significatifs (normalisés) d'un nom, via le tokenizer spaCy."""
    texte = re.sub(r"\(.*?\)", " ", texte)            # "(ouest - est)" : descripteur
    texte = re.sub(r"sans nom", " ", texte, flags=re.I)
    res = []
    for tok in doc(texte):
        if tok.is_punct or tok.is_space:
            continue
        for morceau in re.split(r"[-'’]", normaliser(tok.text)):
            morceau = morceau.strip(".,;:!?\"")
            if morceau and morceau not in MOTS_VIDES:
                res.append(morceau)
    return tuple(res)


@lru_cache(maxsize=None)
def lemmes(texte: str) -> tuple[str, ...]:
    """Lemmes normalisés des mots pleins (et formes de surface) d'un texte."""
    res = []
    for tok in doc(texte):
        if tok.is_punct or tok.is_space or tok.is_stop:
            continue
        for forme in {normaliser(tok.lemma_), normaliser(tok.text)}:
            if forme and forme not in MOTS_VIDES:
                res.append(forme)
    return tuple(res)


def poids_token(tok: str) -> float:
    return POIDS_GENERIQUE if tok in GENERIQUES else 1.0


def sim_tokens(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if any(c.isdigit() for c in a + b) or min(len(a), len(b)) < 4:
        return 0.0                                     # codes routiers : exact
    r = difflib.SequenceMatcher(None, a, b).ratio()
    return r if r >= SEUIL_TOKEN else 0.0


def sim_vecteur(a: str, b: str) -> float:
    if not A_VECTEURS:
        return 0.0
    va, vb = NLP.vocab[a], NLP.vocab[b]
    if not (va.has_vector and vb.has_vector):
        return 0.0
    return float(va.similarity(vb))


def similarite_nom(nom_vt: str, candidat: str) -> float:
    """Similarité entre un nom de la VT et un nom cité (0..1). Un sigle entre
    parenthèses dans la VT (« …chaussées(ENPC) ») sert d'alias."""
    alias = [a for a in re.findall(r"\(([^)]*)\)", nom_vt) if CODE_ROUTE.match(a)]
    return max(_similarite(n, candidat) for n in [nom_vt] + alias)


def _similarite(nom_vt: str, candidat: str) -> float:
    t_vt, t_c = tokens_nom(nom_vt), tokens_nom(candidat)
    if not t_vt or not t_c:
        return 0.0

    def couverture(src, cible):
        tot = sum(poids_token(t) for t in src)
        ok = sum(poids_token(t) * max(sim_tokens(t, c) for c in cible) for t in src)
        return ok / tot

    rappel, precision = couverture(t_vt, t_c), couverture(t_c, t_vt)
    score = 0.7 * rappel + 0.3 * precision
    # « Rue de la Butte Verte » ≠ « Parc de la Butte Verte »
    h_vt, h_c = tete(t_vt), tete(t_c)
    if h_vt and h_c and famille_mot(h_vt) != famille_mot(h_c):
        score *= 0.75
    global_ = difflib.SequenceMatcher(None, " ".join(t_vt), " ".join(t_c)).ratio()
    return max(score, global_ if global_ >= 0.9 else 0.0)


CODE_ROUTE = re.compile(r"^\s*[ADNE]\s?\d{1,4}\b|^\s*[A-Z]{2,6}\s*$")


def tete(tokens: tuple[str, ...]) -> str | None:
    return tokens[0] if tokens and tokens[0] in GENERIQUES else None


def famille_mot(mot: str) -> str:
    for nom_famille, termes in FAMILLES.items():
        if mot in termes:
            return nom_famille
    return mot


def est_anonyme_vt(nom: str) -> bool:
    """Élément de la VT sans nom propre : « route sans nom », « 3 etangs », « forêt »…"""
    return "sans nom" in nom.lower() or nom.strip() == nom.strip().lower()


def a_nom_propre(nom: str) -> bool:
    """Un nom cité contient-il un nom propre ? (majuscule après le 1er mot, ou code routier)"""
    nom = nom.strip()
    if CODE_ROUTE.match(nom):
        return True
    mots = [m for m in re.split(r"[\s'’-]+", nom) if m]
    if not mots or not tokens_nom(nom):
        return False
    premier_propre = (mots[0][0].isupper()
                      and normaliser(mots[0]) not in GENERIQUES | MOTS_VIDES)
    return premier_propre or any(m[0].isupper() for m in mots[1:])


# --------------------------------------------------------------------------- #
# Zones cardinales
# --------------------------------------------------------------------------- #

def zones_vt(champ: str) -> set[str] | None:
    champ = champ.strip()
    if champ.lower() == "toutes":
        return None                                    # toute la carte
    return {z.strip().upper() for z in champ.split(";") if z.strip().upper() in GRILLE}


def extraire_zones(texte: str) -> set[str]:
    """Positions cardinales citées dans un texte (« au nord-est », « centre-sud »,
    « orientée Nord-Sud », « d'ouest en est »…)."""
    t = " " + normaliser(texte) + " "
    zones: set[str] = set()

    def consommer(motif, z):
        nonlocal t
        if re.search(motif, t):
            zones.update(z)
            t = re.sub(motif, " ", t)

    # Orientations / traversées : on couvre les deux extrémités et le centre
    consommer(r"nord[\s-]*ouest\s*[/-]\s*sud[\s-]*est|nord[\s-]*ouest au sud[\s-]*est", {"NO", "C", "SE"})
    consommer(r"sud[\s-]*est\s*[/-]\s*nord[\s-]*ouest|sud[\s-]*est au nord[\s-]*ouest", {"NO", "C", "SE"})
    consommer(r"nord[\s-]*est\s*[/-]\s*sud[\s-]*ouest|nord[\s-]*est au sud[\s-]*ouest", {"NE", "C", "SO"})
    consommer(r"sud[\s-]*ouest\s*[/-]\s*nord[\s-]*est|sud[\s-]*ouest au nord[\s-]*est", {"NE", "C", "SO"})
    consommer(r"\b(nord\s*[/-]\s*sud|sud\s*[/-]\s*nord|du nord au sud|du sud au nord)\b", {"N", "C", "S"})
    consommer(r"\b(est\s*[/-]\s*ouest|ouest\s*[/-]\s*est|d'ouest en est|d'est en ouest|"
              r"de l'ouest a l'est|de l'est a l'ouest)\b", {"O", "C", "E"})
    # Directions composées
    for motif, z in ((r"nord[\s-]*ouest", "NO"), (r"nord[\s-]*est", "NE"),
                     (r"sud[\s-]*ouest", "SO"), (r"sud[\s-]*est", "SE")):
        consommer(r"\b" + motif + r"\b", {z})
    # Directions simples ("est" seulement s'il ne s'agit pas du verbe être)
    consommer(r"\bcentr(e|al|ale)\b", {"C"})
    consommer(r"\bmilieu\b", {"C"})
    consommer(r"\bnord\b", {"N"})
    consommer(r"\bsud\b", {"S"})
    consommer(r"\bouest\b", {"O"})
    consommer(r"(?:\bl'|\bd'|-|/|\ben |\bvers l')est\b|\best\s*[-/)]", {"E"})
    return zones


def score_zone(predites: set[str], attendues: set[str] | None) -> float | None:
    if attendues is None:
        return 1.0
    if not predites or not attendues:
        return None
    if predites & attendues:
        return 1.0
    dist = min(max(abs(GRILLE[p][0] - GRILLE[a][0]), abs(GRILLE[p][1] - GRILLE[a][1]))
               for p in predites for a in attendues)
    return 0.5 if dist == 1 else 0.0


# --------------------------------------------------------------------------- #
# Lecture des fichiers
# --------------------------------------------------------------------------- #

@dataclass
class ElementVT:
    scene: str
    categorie: str
    nom: str
    zones: set[str] | None
    importance: int
    visibilite: dict[str, str]

    @property
    def poids(self) -> float:
        return POIDS_IMPORTANCE[self.importance]


def lire_vt(chemin: Path) -> list[ElementVT]:
    elements, vus = [], set()
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        for ligne in csv.DictReader(f):
            ligne = {k.strip(): (v or "").strip() for k, v in ligne.items() if k}
            if not ligne.get("scene") or not ligne.get("nom"):
                continue
            cle = (ligne["scene"], ligne["categorie"], normaliser(ligne["nom"]), ligne["zones"])
            if cle in vus:                              # doublons dans la VT
                continue
            vus.add(cle)
            try:
                importance = int(ligne.get("importance") or IMPORTANCE_DEFAUT)
            except ValueError:
                importance = IMPORTANCE_DEFAUT
            if not IMPORTANCE_MIN <= importance <= IMPORTANCE_MAX:
                print(f"[!] VT : importance {importance} hors [{IMPORTANCE_MIN}-{IMPORTANCE_MAX}] "
                      f"pour « {ligne['nom']} » ({ligne['scene']}), ramenée à {IMPORTANCE_DEFAUT}",
                      file=sys.stderr)
                importance = IMPORTANCE_DEFAUT
            elements.append(ElementVT(
                scene=ligne["scene"].lower(),
                categorie=ligne["categorie"].lower(),
                nom=ligne["nom"],
                zones=zones_vt(ligne["zones"]),
                importance=importance,
                visibilite={s: (ligne.get(f"visible_{s}") or "0").upper() for s in SERVICES},
            ))
    return elements


@dataclass
class Mention:
    section: str
    texte: str
    noms: list[str]                 # noms cités en tête de puce (gras, avant « : »)
    zones: set[str]
    secondaires: list[str] = field(default_factory=list)   # autres entités de la ligne

    @property
    def tous_noms(self) -> list[str]:
        return self.noms + self.secondaires


@dataclass
class Description:
    scene: str
    service: str
    texte: str
    mentions: list[Mention] = field(default_factory=list)
    sections: dict[str, str] = field(default_factory=dict)


ENTETE = re.compile(r"^\s*[—–\-]{2,}\s*([A-Za-z0-9]+_z\d+)_(google|apple|osm)\s*$", re.I)


def lire_sortie(chemin: Path) -> list[Description]:
    descriptions: list[Description] = []
    courante: list[str] | None = None
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        m = ENTETE.match(ligne)
        if m:
            courante = []
            descriptions.append(Description(m.group(1).lower(), m.group(2).lower(), ""))
            descriptions[-1]._lignes = courante  # type: ignore[attr-defined]
        elif courante is not None:
            courante.append(ligne)
    for d in descriptions:
        d.texte = "\n".join(d._lignes)  # type: ignore[attr-defined]
        d.sections = decouper_sections(d.texte)
        d.mentions = extraire_mentions(d.sections)
    return descriptions


def decouper_sections(texte: str) -> dict[str, str]:
    sections, cle = {k: "" for k in SECTIONS}, "vue"
    for ligne in texte.splitlines():
        if ligne.lstrip().startswith("#"):
            titre = normaliser(ligne.strip("# "))
            cle = ("axes" if "axe" in titre or "voirie" in titre else
                   "reperes" if "repere" in titre else
                   "incertitude" if "incertitude" in titre else
                   "vue" if "ensemble" in titre else cle)
            continue
        sections[cle] += ligne + "\n"
    return sections


def noms_cites(ligne: str) -> tuple[list[str], list[str], str]:
    """Noms cités en tête de puce, autres entités de la ligne, et reste de la ligne
    (où chercher la position)."""
    gras = re.findall(r"\*\*(.+?)\*\*", ligne)
    if gras:
        noms, reste = gras, re.sub(r"\*\*(.+?)\*\*", " ", ligne)
    elif ":" in ligne:
        avant, reste = ligne.split(":", 1)
        noms = [avant]
    elif "(" in ligne:
        avant, reste = ligne.split("(", 1)
        noms = [avant]
    else:
        noms, reste = [ligne], ""
    # Codes / sigles entre parenthèses : "Autoroute de l'Est (A4)", "ENPC (École …)"
    for n in list(noms):
        for contenu in re.findall(r"\(([^)]*)\)", n):
            if CODE_ROUTE.match(contenu) or a_nom_propre(contenu):
                noms.append(contenu)
    noms = [re.sub(r"\(.*?\)", " ", n).strip(" -*") for n in noms]
    # Entités (spaCy) et codes routiers ailleurs dans la ligne
    secondaires = [e.text for e in doc(reste).ents if e.label_ in ("LOC", "ORG", "MISC", "PER")]
    secondaires += re.findall(r"\b[ADN]\s?\d{1,4}\b", reste)
    return [n for n in noms if n], secondaires, reste


def extraire_mentions(sections: dict[str, str]) -> list[Mention]:
    mentions = []
    for cle in ("axes", "reperes"):
        for ligne in sections[cle].splitlines():
            ligne = ligne.strip()
            if not re.match(r"^([-*•]|\d+[.)])\s+", ligne):
                continue
            ligne = re.sub(r"^([-*•]|\d+[.)])\s+", "", ligne)
            noms, secondaires, reste = noms_cites(ligne)
            mentions.append(Mention(cle, ligne, noms, extraire_zones(reste), secondaires))
    # Vue d'ensemble : une mention par phrase, noms = entités spaCy
    for phrase in doc(sections["vue"].strip()).sents:
        texte = phrase.text.strip()
        if not texte:
            continue
        entites = [e.text for e in phrase.ents if e.label_ in ("LOC", "ORG", "MISC")]
        mentions.append(Mention("vue", texte, [], extraire_zones(texte), entites))
    return mentions


# --------------------------------------------------------------------------- #
# Appariement
# --------------------------------------------------------------------------- #

def famille_de(element: ElementVT) -> set[str]:
    mots = set(tokens_nom(element.nom)) | set(lemmes(re.sub(r"\(.*?\)", " ", element.nom)))
    familles = set()
    for nom_famille, termes in FAMILLES.items():
        if mots & termes:
            familles |= termes
    if not familles:
        familles = {m for m in mots if m in GENERIQUES} or {element.categorie}
    return familles


def contient_terme(mention: Mention, termes: set[str]) -> tuple[bool, bool]:
    """(trouvé, au pluriel) : la mention contient-elle un terme de la famille ?"""
    texte = normaliser(mention.texte)
    for tok in doc(mention.texte):
        formes = {normaliser(tok.lemma_), normaliser(tok.text)}
        if formes & termes:
            return True, tok.morph.get("Number") == ["Plur"] or "nombreu" in texte
    for terme in termes:
        if " " in terme and terme in texte:
            return True, "nombreu" in texte
    return False, False


def mention_generique(mention: Mention) -> bool:
    """Une puce est générique si le nom cité ne contient aucun nom propre."""
    if mention.section == "vue":
        return True
    return not any(a_nom_propre(n) for n in mention.noms)


def score_cadrage(element: ElementVT, description: Description) -> float:
    cibles = [l for l in dict.fromkeys(lemmes(element.nom))]
    if not cibles:
        return 0.0
    texte = description.sections["vue"] + description.sections["axes"] + description.sections["reperes"]
    dispo = set(lemmes(texte))
    trouves = 0.0
    for c in cibles:
        candidats = {c} | SYNONYMES.get(c, set())
        if candidats & dispo or any(sim_tokens(c, d) for d in dispo):
            trouves += 1
        elif any(sim_vecteur(c, d) >= SEUIL_VECTEUR for d in dispo):
            trouves += 0.5
    return trouves / len(cibles)


@dataclass
class Resultat:
    element: ElementVT
    attendu: str               # N / T
    trouve: float = 0.0
    zone: float | None = None
    mention: str = ""
    methode: str = ""


def evaluer(description: Description, vt: list[ElementVT]) -> dict:
    service = description.service
    scene_vt = [e for e in vt if e.scene == description.scene]
    attendus = [e for e in scene_vt if e.visibilite[service] in ("N", "T")]
    resultats: list[Resultat] = []
    mentions_singulieres_utilisees: set[int] = set()

    # 1. éléments nommés et cadrage
    generiques_a_traiter = []
    for e in attendus:
        r = Resultat(e, e.visibilite[service])
        if e.categorie == "cadrage":
            s = score_cadrage(e, description)
            if s >= SEUIL_CADRAGE:
                r.trouve, r.zone, r.methode = s, None, "cadrage"
        elif not est_anonyme_vt(e.nom):
            meilleur, mention_m = 0.0, None
            for m in description.mentions:
                for n in m.tous_noms:
                    s = similarite_nom(e.nom, n)
                    if s > meilleur:
                        meilleur, mention_m = s, m
            if meilleur >= SEUIL_NOM and mention_m is not None:
                r.trouve, r.methode, r.mention = 1.0, f"nom ({meilleur:.2f})", mention_m.texte
                r.zone = score_zone(mention_m.zones, e.zones)
        if r.trouve == 0 and r.methode != "cadrage" and (r.attendu == "T" or est_anonyme_vt(e.nom)):
            generiques_a_traiter.append(r)
        resultats.append(r)

    # 2. éléments anonymes / seulement tracés : mention générique dans la bonne zone
    for r in sorted(generiques_a_traiter, key=lambda r: -r.element.poids):
        termes = famille_de(r.element)
        meilleur, idx_m, m_m = 0.0, None, None
        for i, m in enumerate(description.mentions):
            if not mention_generique(m):
                continue
            ok, pluriel = contient_terme(m, termes)
            if not ok:
                continue
            if not pluriel and i in mentions_singulieres_utilisees:
                continue
            z = score_zone(m.zones, r.element.zones)
            s = 0.5 if z is None else z
            if s > meilleur:
                meilleur, idx_m, m_m = s, i, (m, pluriel)
        if meilleur > 0 and m_m is not None:
            r.trouve, r.methode, r.mention = meilleur, "générique", m_m[0].texte
            if not m_m[1]:
                mentions_singulieres_utilisees.add(idx_m)

    # 3. précision sur les puces nommées (AXES, REPÈRES)
    precision_detail = []
    for m in description.mentions:
        if m.section == "vue" or not m.noms or not a_nom_propre(m.noms[0]):
            continue
        meilleur, elt = 0.0, None
        for e in scene_vt:
            if e.categorie == "cadrage" or est_anonyme_vt(e.nom):
                continue
            s = max(similarite_nom(e.nom, n) for n in m.noms)
            if s > meilleur:
                meilleur, elt = s, e
        if meilleur >= SEUIL_NOM and elt is not None:
            statut = "correct" if elt.visibilite[service] in ("N", "T") else "hors service"
        else:
            statut, elt = "non vérifié", None
        precision_detail.append((m.noms[0], statut, elt))

    # Scores
    poids_tot = sum(r.element.poids for r in resultats)
    rappel = sum(r.element.poids * r.trouve for r in resultats) / poids_tot if poids_tot else 0.0
    zones = [(r.element.poids, r.zone) for r in resultats
             if r.trouve and r.zone is not None and r.methode.startswith("nom")]
    localisation = (sum(p * z for p, z in zones) / sum(p for p, _ in zones)) if zones else None
    valeurs = {"correct": 1.0, "hors service": 0.5, "non vérifié": 0.0}
    precision = (sum(valeurs[s] for _, s, _ in precision_detail) / len(precision_detail)
                 if precision_detail else None)

    composantes = {"rappel": rappel, "precision": precision, "localisation": localisation}
    dispo = {k: v for k, v in composantes.items() if v is not None}
    total_poids = sum(POIDS_NOTE[k] for k in dispo)
    note = 20 * sum(POIDS_NOTE[k] * v for k, v in dispo.items()) / total_poids if total_poids else 0.0

    return {
        "scene": description.scene, "service": description.service, "note": note,
        "rappel": rappel, "precision": precision, "localisation": localisation,
        "nb_attendus": len(resultats), "nb_trouves": sum(1 for r in resultats if r.trouve),
        "nb_cites": len(precision_detail), "resultats": resultats, "precision_detail": precision_detail,
    }


# --------------------------------------------------------------------------- #
# Affichage
# --------------------------------------------------------------------------- #

def pct(v):
    return "  n/a" if v is None else f"{100 * v:5.1f}%"


def afficher(ev: dict, detail: bool):
    print(f"\n=== {ev['scene']} / {ev['service']} ===  note : {ev['note']:.2f}/20")
    print(f"  rappel pondéré : {pct(ev['rappel'])}  ({ev['nb_trouves']}/{ev['nb_attendus']} éléments visibles retrouvés)")
    print(f"  précision      : {pct(ev['precision'])}  ({ev['nb_cites']} éléments nommés cités)")
    print(f"  localisation   : {pct(ev['localisation'])}")
    if not detail:
        return
    print("  -- Éléments de la VT retrouvés --")
    for r in ev["resultats"]:
        if r.trouve:
            z = "" if r.zone is None else f" zone={r.zone:.1f}"
            print(f"    [+] ({r.attendu}, imp {r.element.importance}) {r.element.nom.strip()} "
                  f"<- {r.methode}{z} | « {r.mention[:70]} »")
    print("  -- Éléments de la VT manqués --")
    for r in ev["resultats"]:
        if not r.trouve:
            print(f"    [-] ({r.attendu}, imp {r.element.importance}) {r.element.categorie}: {r.element.nom.strip()}")
    print("  -- Éléments cités --")
    for nom, statut, elt in ev["precision_detail"]:
        lien = f" = {elt.nom.strip()}" if elt else ""
        print(f"    [{statut}] {nom}{lien}")


def ecrire_csv(evaluations: list[dict], chemin: Path):
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scene", "service", "note_20", "rappel", "precision", "localisation",
                    "nb_attendus", "nb_trouves", "nb_cites"])
        for ev in evaluations:
            w.writerow([ev["scene"], ev["service"], f"{ev['note']:.2f}"] +
                       ["" if ev[k] is None else f"{ev[k]:.3f}" for k in ("rappel", "precision", "localisation")] +
                       [ev["nb_attendus"], ev["nb_trouves"], ev["nb_cites"]])


def main():
    ici = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description="Note les descriptions de cartes par rapport à la VT.")
    p.add_argument("sortie", nargs="?", default=ici / "sortie.txt", type=Path)
    p.add_argument("vt", nargs="?", default=ici / "VT.csv", type=Path)
    p.add_argument("--detail", action="store_true", help="liste les éléments trouvés / manqués")
    p.add_argument("--csv", type=Path, help="écrit les notes dans un fichier CSV")
    args = p.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    vt = lire_vt(args.vt)
    scenes_vt = {e.scene for e in vt}
    evaluations = []
    for d in lire_sortie(args.sortie):
        if d.scene not in scenes_vt:
            print(f"\n[!] {d.scene}_{d.service} : scène absente de la VT, ignorée.")
            continue
        ev = evaluer(d, vt)
        evaluations.append(ev)
        afficher(ev, args.detail)

    if evaluations:
        moyenne = sum(ev["note"] for ev in evaluations) / len(evaluations)
        print(f"\nMoyenne : {moyenne:.2f}/20 sur {len(evaluations)} description(s)")
    if args.csv:
        ecrire_csv(evaluations, args.csv)
        print(f"Notes écrites dans {args.csv}")


if __name__ == "__main__":
    main()
