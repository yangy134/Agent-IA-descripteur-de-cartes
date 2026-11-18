from pathlib import Path
import json
import os

racine = "executions"

def creation_prompt(id_exec):
    """
    entrée: un int représentant l'identifiant de l'exécution en cours
    sortie: un string représentant le prompt que le souhaite donner à l'IA finale
    """
    ## Variables de base
    prompt_final = ""
    ## Récupération du dossier d'exécution
    chemin_dossier = os.path.join(racine, "Exec_" + str(id_exec))
    ## concaténation de toutes les réponses dans un texte

    pass







if __name__ == "__main__":

    print("hello world")