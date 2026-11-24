# 🛠️ Tester le pipeline C1 dans VS Code

Ce guide vous montre, pas à pas, comment lancer **main.py** (le pipeline C1) depuis Visual Studio Code et récupérer la description accessible générée.

---

## 1️⃣ Prérequis

- **VS Code** installé (https://code.visualstudio.com/).
- **Python 3.10+** installé.
- Le dépôt du projet déjà cloné : `C:\\Users\\pc\\Desktop\\GeoAI_Carto`.
- Une clé d'API OpenRouter (ou tout autre service que vous utilisez) disponible dans un fichier **.env** :
  ```
  OPENROUTER_API_KEY=ma_cle_api
  ```
  > Le fichier `.env` est déjà listé dans `.gitignore` pour éviter de le committer.

---

## 2️⃣ Ouvrir le projet dans VS Code

1. Lancez VS Code.
2. `Fichier → Ouvrir le dossier…` et sélectionnez `C:\\Users\\pc\\Desktop\\GeoAI_Carto`.
3. Le volet *Explorateur* doit afficher les dossiers `src/`, le script `main.py`, le fichier `requirements.txt`, etc.

---

## 3️⃣ Configurer l’interpréteur Python

1. Ouvrez la palette de commandes (`Ctrl+Shift+P`).
2. Tapez **Python: Sélectionner l’interpréteur**.
3. Choisissez l’interpréteur de votre environnement virtuel (par ex. `.venv\\Scripts\\python.exe`).
   - Si vous n’avez pas d’environnement virtuel, créez‑en un :
     ```powershell
     python -m venv .venv
     .venv\\Scripts\\activate
     ```
4. Une fois l’interpréteur sélectionné, le coin inférieur gauche de VS Code affichera le chemin de l’interpréteur.

---

## 4️⃣ Installer les dépendances

Dans le **Terminal intégré** (`Ctrl+` ``) exécutez :
```powershell
pip install -r requirements.txt
```
> Le fichier `requirements.txt` doit contenir les packages nécessaires (ex. `openai`, `torch`, etc.).

---

## 5️⃣ Vérifier le fichier `.env`

Assurez‑vous que le fichier `.env` contenant votre clé d’API se trouve à la racine du projet :
```
C:\\Users\\pc\\Desktop\\GeoAI_Carto\\.env
```
VS Code charge automatiquement les variables d’environnement du fichier `.env` grâce à l’extension **Python**.

---

## 6️⃣ Exécuter le script depuis le terminal

```powershell
python main.py --image maps/google_maps/Map1_GoogleMaps.png
```
- Le script crée le dossier `outputs/` s’il n’existe pas.
- Le résultat s’affiche dans le terminal et est également écrit dans `outputs/Map1_GoogleMaps_accessible_desc.txt`.

---

## 7️⃣ Configuration de lancement (optionnelle) : `launch.json`

Pour pouvoir lancer le script via le bouton **Run** ou le débogueur :
1. Créez le dossier `.vscode` à la racine du projet (s’il n’existe pas).
2. Ajoutez le fichier `launch.json` :
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run C1 Pipeline",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "args": ["--image", "maps/google_maps/Map1_GoogleMaps.png"],
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env"
        }
    ]
}
```
3. Ouvrez le panneau **Run & Debug** (`Ctrl+Shift+D`), choisissez **Run C1 Pipeline** puis cliquez sur le bouton ▶️.
   - Vous verrez la même sortie qu’en ligne de commande, mais vous pourrez aussi placer des points d’arrêt dans le code pour le déboguer.

---

## 8️⃣ Vérifier la sortie

- Le texte généré apparaît dans le terminal.
- Le fichier de sortie se trouve dans le dossier `outputs/` ; vous pouvez l’ouvrir directement depuis l’explorateur VS Code.

---

## 9️⃣ Astuces rapides

- **Rafraîchir l’interpréteur** : si vous créez ou modifiez le `.env`, redémarrez VS Code ou relancez le terminal.
- **Nettoyage** : supprimez le dossier `outputs/` entre deux tests si vous voulez repartir d’une ardoise vierge.
- **Mode debug** : ajoutez des `print()` où vous le souhaitez ou utilisez le débogueur pour inspecter les variables intermédiaires (`result`, `pipeline`, etc.).

---

Voilà ! Vous avez toutes les étapes nécessaires pour tester le pipeline C1 dans VS Code, visualiser le résultat et, si besoin, le déboguer.

*Bonne exploration !*