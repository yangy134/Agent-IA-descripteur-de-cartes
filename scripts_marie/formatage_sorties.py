from pathlib import Path
import json
import os

def recuperation_metadonnees(nom_fichier_reponse):
    """
    Récupère les métadonnées de la réponse brute 
    contenue dans le nom du fichier
    """
    ## Découpage du nom de fichier
    tab_meta = nom_fichier_reponse.split("_")
    dict_meta = { "Nom carte": tab_meta[0], "Nom LLM": tab_meta[1], "Nb tour": tab_meta[2], "Nb Répétition Prompt": tab_meta[3], "Nb Prompt": tab_meta[4] }
    return dict_meta


def conversion_sortie_json(chemin_fichier_reponse):
    """
    Convertie un fichier de données brutes 
    en sortie json formatée 
    --> s'aide de la fonction "recuperation_metadonnees" créée plus haut
    """
    ## Récupération des métadonnées dans le nom du fichier
    nom_fichier = Path(chemin_fichier_reponse).name.split(".")[0]
    dict_fichier = recuperation_metadonnees(nom_fichier)
    ## Récupération du texte à l'intérieur
    contenu_fichier = ""
    with open(chemin_fichier_reponse, 'r', encoding = "utf-8") as f:
        contenu_fichier = f.read()

    ## Création du chemin de sortie
    nom_fichier_sortie  = dict_fichier["Nom carte"] + "_" + dict_fichier["Nom LLM"] + "_" + dict_fichier["Nb tour"] + "_" + dict_fichier["Nb Répétition Prompt"] + "_" + dict_fichier["Nb Prompt"] + "_Sortie.json"
    chemin_sortie = os.path.join(Path(chemin_fichier_reponse).parent.parent, "data_sorties", nom_fichier_sortie)


    ## Création d'un fichier json
    dict_fichier["réponse"] = contenu_fichier
    with open(chemin_sortie, "w", encoding="utf-8") as f:
        json.dump(dict_fichier, f, ensure_ascii=False, indent=4)
    



def formatage_sorties(chemin_execution):
    """
    Fonction principale qui prend toutes les réponses brutes d'une exécution
    et qui les formate en json et les enregistre dans le bon dossier (data_sorties)
    """
    ## Pour chaque fichier dans exécution
    contenu_reponses_brutes = os.listdir(os.path.join(chemin_execution, "data_reponses_brutes"))
    for elt in contenu_reponses_brutes:
        conversion_sortie_json(os.path.join(chemin_execution, "data_reponses_brutes", elt))



if __name__ == "__main__" : 
    print("hello world")

    ## Tests 
    chemin_meta = "executions\Exec_20261021115248\data_reponses_brutes\FausseCarte_Humain_1_1_1_ReponseBrute.txt"

    ## test enregistrement fichier JSON
    chemin_sortie = "executions\Exec_20261021115248\data_sorties\FausseCarte_Humain_1_1_1_Sortie.json"
    #conversion_sortie_json(chemin_meta)

    ## Tests enregsitrements de tous les fichiers
    formatage_sorties("executions\Exec_20261021115248")