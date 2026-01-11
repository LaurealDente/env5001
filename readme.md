# Calcul d'énergie

L'objectif du projet est de calculer la consommation d'énergie à partir des données stockés dans le dossier data de ce projet.
La méthodologie se base sur les recherches faites dans le drive partagé.

## Structure

```
.
├── api.py                 # Contrôleur (interface publique)
├── interface.py           # Vue (formatage résultats)
├── traitement.py          # Métier (calculs + parsing)
└── config/
    ├── config.yaml        # Config régions/providers
    └── config_model.yaml  # Config modèles
```

## Utilisation

### API

Lancement d'une API web qui appelle notamment le traitement.py pour répondre à des statistiques d'entrée.

### Interface

Interface avec les mêmes fonctionnalités que l'API, avec des appels à traitement.py mais par l'intermédiaire d'un appel python. Il faut pouvoir prendre ce script comme une librairie.

### Traitement

Centre de calcul qui rassemble les appels et renvoie les valeurs nécessaires

## Configuration

### Configuration basique

La configuration basique contiendra par les chemins de sauvergarde données par exemple pour créer un historique des calculs.
En général ce seront les paramètres liés au codage du projet et les fichiers .py

# Configuration des modeles 

La configuration des modeles contiendra les valeurs de consommation en fonction des pays (PUE), consommation moyenne par modeles... tout ce qui permet de faire les calculs selon la méthodologie dévelopée dans le google drive.