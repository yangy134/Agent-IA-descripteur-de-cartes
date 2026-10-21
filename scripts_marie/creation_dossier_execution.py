import datetime
import os

def crea_doss_exec():
    """
    Créé le dossier si contiendra les données de l'exécution 
    --> Voir schéma pour la structure de ce dossier et document méthodologie sur le Drive
    pour les formatages des noms et contenu de fichiers
    """

    ## Localisation de la racine
    racine = "executions"

    ## Récupération des données de date
    maintenant = datetime.datetime.now()
    nom_dossier = "Exec_" + maintenant.strftime("%Y%m%d%H%M%S")
    print(nom_dossier)

    ## Création du dossier principal
    os.mkdir( os.path.join(racine, nom_dossier))
    chemin_dossier = os.path.join(racine, nom_dossier)

    ## Création des sous-dossiers
    os.mkdir( os.path.join(chemin_dossier, "data_reponses_brutes"))
    os.mkdir( os.path.join(chemin_dossier, "data_sorties"))
    print("dossier complet créé")

    ## Ajout des métadonnées
    chemin_metadonnees = os.path.join(chemin_dossier, "metadonnees_execution.txt")
    with open(chemin_metadonnees, "w") as f: 
        f.writelines("test")
        




if __name__ == "__main__":
    crea_doss_exec()