import yaml
from pathlib import Path
from typing import Dict, Any


# =========================
# Chargement YAML
# =========================

def load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_configs():
    config = load_yaml(Path("config/config.yaml"))
    config_model = load_yaml(Path("config/config_model.yaml"))
    return config, config_model


def load_analytics(config: Dict[str, Any]) -> Dict[str, Any]:
    data_path = Path(config["paths"]["data_dir"]) / config["paths"]["analytics_file"]
    return load_yaml(data_path)


# =========================
# Calculs unitaires
# =========================

def characters_to_tokens(characters: int) -> float:
    return characters / 4.0


def compute_inference_time_s(profile: Dict[str, Any]) -> float:
    tokens_in = characters_to_tokens(profile["input_characters"])
    tokens_out = characters_to_tokens(profile["output_characters"])
    return (tokens_in + tokens_out) / profile["throughput_tokens_per_s"]


def compute_energy_kwh(
    power_w: float,
    time_s: float,
    eta: float,
    pue: float
) -> float:
    energy_wh = (power_w * time_s) / eta
    return (energy_wh / 3600) * pue


def compute_carbon_gco2e(
    energy_kwh: float,
    carbon_intensity: float
) -> float:
    return energy_kwh * carbon_intensity


# =========================
# Calcul métier principal
# =========================

def compute_profile(
    profile_key: str,
    entries: list,
    config: Dict[str, Any],
    config_model: Dict[str, Any],
    region_name: str
) -> Dict[str, Any]:

    region = config["regions"][region_name]
    profile_name = profile_key.rstrip("s")  # chatbots → chatbot
    profile = config_model["profiles"][profile_name]
    gpu = config_model["hardware"]["gpu"]

    time_per_inference = compute_inference_time_s(profile)

    daily_results = {}
    totals = {
        "inferences": 0,
        "energy_kwh": 0.0,
        "carbon_gco2e": 0.0
    }

    for entry in entries:
        date = entry["date"]
        count = entry["count"]

        energy = compute_energy_kwh(
            power_w=gpu["power_w"],
            time_s=time_per_inference * count,
            eta=gpu["eta"],
            pue=region["pue"]
        )

        carbon = compute_carbon_gco2e(
            energy_kwh=energy,
            carbon_intensity=region["carbon_intensity_g_per_kwh"]
        )

        daily_results[date] = {
            "inferences": count,
            "energy_kwh": energy,
            "carbon_gco2e": carbon
        }

        totals["inferences"] += count
        totals["energy_kwh"] += energy
        totals["carbon_gco2e"] += carbon

    return {
        "profile": profile_name,
        "region": region_name,
        "daily": daily_results,
        "totals": totals
    }


def run_energy_calculation(region: str = None) -> Dict[str, Any]:
    config, config_model = load_configs()
    analytics = load_analytics(config)

    if region is None:
        region = config["default_region"]

    results = {}
    genai = analytics.get("genai", {})

    for profile_key, entries in genai.items():
        # --- AJOUT DE LA SÉCURITÉ ICI ---
        # Si 'entries' n'est pas une liste (ex: la clé 'description'), on l'ignore
        if not isinstance(entries, list):
            continue
            
        results[profile_key] = compute_profile(
            profile_key=profile_key,
            entries=entries,
            config=config,
            config_model=config_model,
            region_name=region
        )

    return results
