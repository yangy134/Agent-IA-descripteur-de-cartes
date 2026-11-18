import datetime
import os
import json
from pathlib import Path

def crea_doss_exec( nom_carte, nb_tours, nb_repetitions, id_serie_prompts):
    """
    Créé le dossier si contiendra les données de l'exécution 
    --> Voir schéma pour la structure de ce dossier et document méthodologie sur le Drive
    pour les formatages des noms et contenu de fichiers
    entrée: nom de la carte (string, ex: nom_carte.png), 
            nombre de tours (int --> toujours 1 pour le moment)
            Nombre de répétitions de la série de prompts (int)
            L'identifiant de la série de prompts (int)
    """

    ## Localisation de la racine
    racine = os.path.join("data","executions")

    ## Récupération des données de date
    maintenant = datetime.datetime.now()
    nom_dossier = "Exec_" + maintenant.strftime("%Y%m%d%H%M%S")
    print(nom_dossier)

    ## Création du dossier principal
    os.mkdir( os.path.join(racine, nom_dossier))
    chemin_dossier_exec = os.path.join(racine, nom_dossier)

    ## Création des sous-dossiers
    os.mkdir( os.path.join(chemin_dossier_exec, "data_reponses_brutes"))
    os.mkdir( os.path.join(chemin_dossier_exec, "data_sorties"))
    print("dossier complet créé")

    ## Ajout des métadonnées dans un dictionnaire
    chemin_metadonnees = os.path.join(chemin_dossier_exec, "metadonnees_execution.json")
    chemin_dossier_carte = os.path.join("data", "cartes")
    chemin_dossier_prompts = os.path.join("data", "prompts", "Series_prompts")
    nom_fichier_serie_prompt = "SeriePrompts_" +  str(id_serie_prompts) + ".json"
    print(nom_carte, os.listdir(Path(chemin_dossier_carte))[0], nom_fichier_serie_prompt)
    if (nom_carte in os.listdir(Path(chemin_dossier_carte))[0]) and ( nom_fichier_serie_prompt in os.listdir(Path(chemin_dossier_prompts))[0]): ## Vérifie que la carte et la série de prompts existent bien
        dict_metadonnees = { "Nom_carte" : nom_carte, "Nb_tours" : nb_tours, "Nb_repetitions": nb_repetitions, "Id_serie_prompts": id_serie_prompts}

    ## Conversion en json et enregistrement
    with open(chemin_metadonnees, "w", encoding="utf-8") as f:
            json.dump(dict_metadonnees, f, ensure_ascii=False, indent=4)




if __name__ == "__main__":
    crea_doss_exec("carte1_rond_point_pyramides.png", 1, 2, 1)