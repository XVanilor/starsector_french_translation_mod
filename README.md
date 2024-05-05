## Starsector - French Translation mod
Mod de traduction FR pour le jeu [StarSector](https://fractalsoftworks.com/).

## Installation

- [Téléchargez le mod au format .zip](https://github.com/XVanilor/starsector_french_translation_mod/archive/refs/heads/main.zip)
- Extraire le .zip et le mettre dans le dossier "mods" de Starsector, situé habituellement dans `C:\Program Files (x86)\Fractal Softworks\Starsector\mods`
- Au lancement du jeu, activer le mod "French Translation"

## Participer à la traduction

Tous les fichiers dans le dossier `data` du mod sont **générés**, il ne faut donc **pas y toucher directement**.

Les fichiers à traduire sont dans le dossier `translations`.

Pour générer les fichiers `data`, il faut lancer le script python :

Sur Windows:
Lancer le fichier `download.bat`

Avec Python:
```sh
python3 src/helper.py fetch
```

## Récupérer les chaines après un patch du jeu

Quand une nouvelle version du jeu sort, il faut récupérer les nouvelles chaines à traduire :

Sur Windows:
Lancer `download.bat`
Écrire les nouvelles traductions qui sont stockées dans `translations`
Lancer `update_data.bat`

Avec Python directement:
```bash
python3 src/helper.py fetch
# Écrire les nouvelles traductions qui sont stockées dans translations
python3 src/help.py write
```

## About
Projet lancé [en 2017 par Neuroxer](https://fractalsoftworks.com/forum/index.php?topic=12799.msg216851#msg216851) puis abandonné.
Il a été repris en 2021 par [grena](https://github.com/grena/starsector_french_translation_mod), mis sur Github pour en faciliter la maintenance et la collaboration puis a été de nouveau arrêté.
Je l'ai repris en 2024 à la suite du lancement par un petit groupe de passionné sur [Discord](https://discord.gg/HzNmt23GrJ)
