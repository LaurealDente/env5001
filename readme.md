# Calcul d’énergie et d’impact carbone (ENV5001)

## Objectif

L’objectif de ce projet est de **calculer la consommation d’énergie (kWh) et l’impact carbone (gCO₂e)** associés à des usages de modèles d’IA générative, à partir de **données d’analytics fournies en entrée**.

La méthodologie de calcul repose sur les travaux et hypothèses définis dans le **drive partagé** (puissance GPU, throughput, PUE, intensité carbone, etc.).

> **Important**  
> L’application **ne stocke pas les données analytics** (ex. Fluid Topics).  
> Elles sont **transmises dynamiquement via une requête HTTP POST** à l’API.

---

## Structure du projet
```bash
.
├── api.py # API REST (FastAPI)
├── interface.py # Interface Python (formatage / librairie)
├── traitement.py # Métier : parsing + calculs énergie & carbone
├── config/
│ ├── config.yaml # Configuration régions / PUE / intensité carbone
│ └── config_model.yaml # Configuration modèles et paramètres matériels
└── README.md
```

---

## Principe général

- Les **configurations** (régions, PUE, modèles, puissances, etc.) sont stockées dans `config/`
- Les **données analytics** (ex. `2025-FluidTopics-daily-analytics.yaml`) sont :
  - transmises à l’API via un `POST`
  - ou injectées via un appel Python (mode librairie)
- Le cœur des calculs est centralisé dans `traitement.py`

---

## Utilisation

### 1. API REST

L’API expose un endpoint principal :

POST /energy


#### Fonctionnement

- Le client envoie un **fichier YAML d’analytics** dans le body de la requête
- L’API :
  1. parse les données
  2. applique la méthodologie de calcul
  3. renvoie les résultats énergie & carbone au format JSON

#### Lancement de l’API

```bash
uvicorn api:app --reload
```

#### Documentation interactive (Swagger) :
```bash
http://127.0.0.1:8000/docs
Exemple d’appel (curl)
curl -X POST "http://127.0.0.1:8000/energy?region=france" \
  -F "analytics_file=@2025-FluidTopics-daily-analytics.yaml"
  ```
  
### 2. Interface Python (mode librairie)
Le projet peut également être utilisé directement en Python, sans passer par l’API REST.

from interface import run

results = run(region="france")
print(results)
Ce mode est utile pour :

des scripts internes

des notebooks

des tests unitaires

### 3. Traitement (cœur métier)
Le fichier traitement.py contient :

le parsing des données analytics (YAML)

le calcul du temps d’inférence

le calcul de la consommation énergétique (kWh)

le calcul de l’impact carbone (gCO₂e)

l’agrégation par jour et par profil

Aucune logique d’API ou d’affichage n’est présente dans ce fichier.

## Configuration
### Configuration basique (config.yaml)
Ce fichier contient :

les régions disponibles

les valeurs de PUE

les intensités carbone (gCO₂/kWh)

la région par défaut

Ces paramètres sont indépendants des modèles.

### Configuration des modèles (config_model.yaml)
Ce fichier contient :

les profils d’usage (chatbot, completion, etc.)

les puissances matérielles (GPU / CPU)

les rendements (η)

les tailles moyennes d’entrées / sorties

les throughputs

Ces valeurs sont utilisées pour appliquer la méthodologie décrite dans le drive partagé.

## Résultats produits
Pour chaque profil :

nombre total d’inférences

consommation énergétique totale (kWh)

impact carbone total (gCO₂e)

détail journalier (si nécessaire)

## Notes RSE
Les calculs sont paramétrables et auditables

Aucune donnée métier sensible n’est stockée

Les hypothèses sont centralisées dans des fichiers de configuration

Le projet est conçu pour être traçable, reproductible et extensible
