from typing import Dict, Any
from traitement import run_energy_calculation


def format_results(results: Dict[str, Any]) -> Dict[str, Any]:
    formatted = {}

    for profile, data in results.items():
        formatted[profile] = {
            "region": data["region"],
            "totals": {
                "inferences": data["totals"]["inferences"],
                "energy_kwh": round(data["totals"]["energy_kwh"], 3),
                "carbon_gco2e": round(data["totals"]["carbon_gco2e"], 1)
            }
        }

    return formatted


def run(region: str = None) -> Dict[str, Any]:
    results = run_energy_calculation(region=region)
    return format_results(results)
