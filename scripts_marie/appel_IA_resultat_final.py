from pathlib import Path
import json
import os

racine = "data"
prompt_choisi = "Prompt_final_1.txt"

def creation_prompt(id_exec):
    """
    entrée: un int représentant l'identifiant de l'exécution en cours
    sortie: un string représentant le prompt que le souhaite donner à l'IA finale
    """

    ## Variables de base
    prompt_final = ""

    ## Récupération du dossier d'exécution
    chemin_dossier_exec = os.path.join(racine, "executions", "Exec_" + str(id_exec))
    chemin_base_prompt_final = os.path.join(chemin_dossier_exec, "Prompts_finaux", prompt_choisi)

    ## Récupération des métadonnées de l'exécution (à faire)


    ## concaténation de toutes les réponses dans un texte
    with open(chemin_base_prompt_final, "r") as f: 
        for line in f:
            prompt_final += line

    return "bonsoir"







if __name__ == "__main__":

    print("hello world")