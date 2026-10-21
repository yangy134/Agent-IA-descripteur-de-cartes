import datetime

def crea_doss_exec():
    """
    Créé le dossier si contiendra les données de l'exécution 
    --> Voir schéma pour la structure de ce dossier et document méthodologie sur le Drive
    pour les formatages des noms et contenu de fichiers
    """
    ## Localisation de la racine
    racine = "../execution"
    ## Récupération des données de date
    maintenant = datetime.datetime.now()
    nom_dossier = "Exec_" + maintenant.strftime("%Y%m%d%H%M%S")
    print(nom_dossier)
    ## Création du dossier principal




if __name__ == "__main__":
    crea_doss_exec()