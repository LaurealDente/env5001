import sys
from pathlib import Path

# On s'assure de pouvoir importer traitement peu importe où on est
try:
    from traitement import Requete, Modele, load_configs
except ImportError:
    # Fallback si lancé depuis un sous-dossier
    sys.path.append(str(Path(__file__).parent))
    from traitement import Requete, Modele, load_configs

# Variable globale pour ne pas recharger les YAML à chaque appel
_GLOBAL_CONFIG = None
_MODEL_CONFIG = None

def _get_configs():
    """Charge les configs une seule fois (Singleton)."""
    global _GLOBAL_CONFIG, _MODEL_CONFIG
    if _GLOBAL_CONFIG is None:
        try:
            _GLOBAL_CONFIG, _MODEL_CONFIG = load_configs()
        except Exception as e:
            print(f"⚠️ Erreur chargement config: {e}")
            return {}, {}
    return _GLOBAL_CONFIG, _MODEL_CONFIG

def calcul_rapide(input_tokens: int, output_tokens: int, region: str = "france", profile_name: str = "chatbot") -> dict:
    """
    LA fonction magique.
    Tu lui donnes juste des chiffres, elle s'occupe de toute la plomberie.
    """
    conf, conf_model = _get_configs()
    
    # 1. Récupération des paramètres (avec valeurs par défaut de sécurité)
    # Région
    region_specs = conf.get("regions", {}).get(region, {"pue": 1.3, "carbon_intensity_g_per_kwh": 60})
    
    # Hardware (On prend GPU par défaut)
    gpu_specs = conf_model.get("hardware", {}).get("gpu", {"power_w": 700, "eta": 0.85})
    cpu_specs = conf_model.get("hardware", {}).get("cpu", {"power_w": 70, "eta": 0.15})
    
    # Profil (pour la vitesse)
    # Si le profil demandé n'existe pas, on prend une vitesse standard de 60 tok/s
    profil_data = conf_model.get("profiles", {}).get(profile_name, {})
    throughput = profil_data.get("throughput_tokens_per_s", 60)
    
    # 2. Création des Objets Métier (C'est ici qu'on cache la complexité)
    req = Requete(name=f"quick_{profile_name}")
    req.add_topics(input_tokens)
    req.output_size = output_tokens
    
    modele = Modele(
        name="Modele_Interface",
        requete=req,
        pue=region_specs["pue"],
        intensite_carbone=region_specs["carbon_intensity_g_per_kwh"],
        utilization_rate=1.0,
        etat_CPU=cpu_specs["eta"],
        power_CPU=cpu_specs["power_w"],
        power_GPU=gpu_specs["power_w"],
        tokens_per_hour=int(throughput * 3600)
    )
    
    # 3. Résultats formatés
    return {
        "input": input_tokens,
        "output": output_tokens,
        "region": region,
        "temps_sec": round(modele.get_t_compute(), 4),
        "energie_kwh": round(modele.get_energie_total() / 3_600_000, 6),
        "co2_g": round(modele.empreinte_requete(), 4)
    }

def formater_resultat(res: dict) -> str:
    """Joli affichage pour le terminal."""
    return (
        f"--- Résultat Calcul ---\n"
        f"📍 Région : {res['region']}\n"
        f"🔄 Volume : {res['input']} in / {res['output']} out\n"
        f"⏱️ Temps  : {res['temps_sec']} s\n"
        f"⚡ Énergie: {res['energie_kwh']} kWh\n"
        f"🌍 Carbone: {res['co2_g']} gCO2e\n"
        f"-----------------------"
    )

# --- Bloc pour tester directement en ligne de commande ---
if __name__ == "__main__":
    import argparse
    
    # Permet de lancer: python interface.py --in 2000 --out 500 --region usa
    parser = argparse.ArgumentParser(description="Calculateur Carbone Simplifié")
    parser.add_argument("--in_tok", type=int, default=1000, help="Tokens en entrée")
    parser.add_argument("--out_tok", type=int, default=500, help="Tokens en sortie")
    parser.add_argument("--region", type=str, default="france", help="Région (france, usa, germany...)")
    
    args = parser.parse_args()
    
    resultat = calcul_rapide(args.in_tok, args.out_tok, args.region)
    print(formater_resultat(resultat))