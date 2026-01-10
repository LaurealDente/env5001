# ENV5001 – Estimation de l’impact énergétique et carbone de l’IA

## Objectif

Ce projet estime l’**impact énergétique (kWh)** et **carbone (CO₂)** de l’usage de l’IA générative dans **Fluid Topics**, à partir de **données d’analytics réelles**.

À partir des usages (chatbot, complétion, traduction), il :
- estime les **tokens consommés**
- calcule la **consommation énergétique**
- déduit les **émissions de CO₂**
- expose les résultats via une **API**, une **interface web** et une **CLI**

---

## Fonctionnalités

- Profils IA : **Chatbot**, **Completion**, **Translation**
- Calculs par jour et par période
- Paramètres de simulation configurables
- API FastAPI + interface web légère
- Interface CLI / librairie Python

---

## Structure

env5001-main/
├── api.py # API + interface web (/ui)
├── traitement.py # Cœur des calculs
├── interface.py # CLI / librairie
├── config/
│ └── config.yaml
├── data/
│ └── analytics.yaml
└── README.md

yaml
Copier le code

---

## Lancer le projet

### Installation
```bash
python -m venv .venv
source .venv/bin/activate   # ou .\.venv\Scripts\Activate.ps1 (Windows)
pip install fastapi uvicorn pyyaml
Lancer l’API
bash
Copier le code
uvicorn api:app --reload
Interface web : http://127.0.0.1:8000/ui

Docs API : http://127.0.0.1:8000/docs

Interface web
Sélection de période

Cartes KPI (Tokens, Énergie, CO₂)

Graphique journalier

Tableau détaillé

Export JSON

CLI
bash
Copier le code
python interface.py summary
python interface.py daily 2025-08-12
python interface.py range 2025-08-12 2025-08-31
Configuration
Les hypothèses (taille des contenus, intensité carbone, etc.) sont définies dans :

arduino
Copier le code
config/config.yaml
Toute modification est automatiquement prise en compte.

Méthodologie
Les calculs suivent une méthodologie documentée, basée sur :

conversion caractères → tokens

estimation tokens → énergie

conversion énergie → CO₂

Objectif : fournir une estimation transparente et reproductible de l’impact environnemental de l’IA.