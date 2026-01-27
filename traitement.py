import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List


# =========================
# Chargement YAML / Configs
# =========================

def load_yaml(path: Path) -> Dict[str, Any]:
    """Charge un fichier YAML local (config)."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Le YAML {path} doit être un mapping (dict) au top-level.")
    return data


def load_configs() -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Charge config générale + config modèles."""
    config = load_yaml(Path("config/config.yaml"))
    config_model = load_yaml(Path("config/config_model.yaml"))
    return config, config_model


def load_analytics_from_disk(config: Dict[str, Any]) -> Dict[str, Any]:
    """Charge le fichier analytics depuis data/ (mode local)."""
    data_path = Path(config["paths"]["data_dir"]) / config["paths"]["analytics_file"]
    with open(data_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("Le YAML analytics doit être un mapping (dict) au top-level.")
    return data


def parse_analytics_yaml_str(yaml_text: str) -> Dict[str, Any]:
    """Parse un YAML analytics fourni en texte (mode API)."""
    data = yaml.safe_load(yaml_text)
    if not isinstance(data, dict):
        raise ValueError("Le YAML analytics doit être un mapping (dict) au top-level.")
    return data


# =========================
# Calculs unitaires
# =========================

def characters_to_tokens(characters: int) -> float:
    """Approximation: 1 token ~ 4 caractères."""
    return characters / 4.0


def compute_inference_time_s(profile: Dict[str, Any]) -> float:
    """Temps d'inférence en secondes = tokens_totaux / throughput (tokens/s)."""
    tokens_in = characters_to_tokens(profile["input_characters"])
    tokens_out = characters_to_tokens(profile["output_characters"])
    total_tokens = tokens_in + tokens_out
    return total_tokens / profile["throughput_tokens_per_s"]


def compute_energy_kwh(power_w: float, time_s: float, eta: float, pue: float) -> float:
    """
    Énergie (kWh) = (P(W) * t(s) / eta) / 3600 * PUE
    """
    energy_wh = (power_w * time_s) / eta
    energy_kwh = energy_wh / 3600
    return energy_kwh * pue


def compute_carbon_gco2e(energy_kwh: float, carbon_intensity_g_per_kwh: float) -> float:
    """Carbone (gCO2e) = énergie (kWh) * intensité (g/kWh)."""
    return energy_kwh * carbon_intensity_g_per_kwh


# =========================
# Calcul métier principal
# =========================

def compute_profile(
    profile_key: str,
    entries: List[Dict[str, Any]],
    config: Dict[str, Any],
    config_model: Dict[str, Any],
    region_name: str
) -> Dict[str, Any]:
    """
    Calcule résultats (daily + totals) pour un profil analytics (ex: chatbots).
    On mappe chatbots -> chatbot via rstrip('s').
    """
    if region_name not in config["regions"]:
        raise ValueError(f"Région inconnue: {region_name}")

    region = config["regions"][region_name]

    profile_name = profile_key.rstrip("s")  # chatbots -> chatbot
    if profile_name not in config_model["profiles"]:
        raise ValueError(f"Profil modèle introuvable dans config_model.yaml: {profile_name}")

    profile = config_model["profiles"][profile_name]
    gpu = config_model["hardware"]["gpu"]

    time_per_inference = compute_inference_time_s(profile)

    daily_results: Dict[str, Any] = {}
    totals = {"inferences": 0, "energy_kwh": 0.0, "carbon_gco2e": 0.0}

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
            carbon_intensity_g_per_kwh=region["carbon_intensity_g_per_kwh"]
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


def run_energy_calculation_from_analytics_dict(
    analytics: Dict[str, Any],
    region: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mode générique : on passe déjà le dict analytics (API ou autre source).
    """
    config, config_model = load_configs()
    if region is None:
        region = config["default_region"]

    results: Dict[str, Any] = {}
    genai = analytics.get("genai", {})

    if not isinstance(genai, dict):
        raise ValueError("La clé 'genai' doit être un mapping (dict).")

    for profile_key, entries in genai.items():
        # Ignore les métadonnées type description: "..."
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


def run_energy_calculation_from_yaml_text(
    yaml_text: str,
    region: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mode API : on passe le contenu YAML en texte (body POST).
    """
    analytics = parse_analytics_yaml_str(yaml_text)
    return run_energy_calculation_from_analytics_dict(analytics, region=region)


def run_energy_calculation(region: Optional[str] = None) -> Dict[str, Any]:
    """
    Mode local (debug) : charge data/2025-FluidTopics-daily-analytics.yaml depuis le disque.
    """
    config, _ = load_configs()
    analytics = load_analytics_from_disk(config)
    return run_energy_calculation_from_analytics_dict(analytics, region=region)
