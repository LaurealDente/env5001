"""
Tests complets du projet de calcul énergétique et carbone.

Ce script teste :
- le chargement des fichiers YAML
- le parsing des analytics
- le calcul métier (énergie + carbone)
- l'interface Python

À lancer depuis la racine du projet :
    python test.py
"""

from traitement import (
    load_configs,
    load_analytics,
    run_energy_calculation
)
from interface import run


def test_configs():
    print("TEST 1 - Chargement des configurations")
    config, config_model = load_configs()

    assert "paths" in config
    assert "regions" in config
    assert "profiles" in config_model

    print("OK - Configurations chargées\n")


def test_analytics():
    print("TEST 2 - Chargement et parsing des analytics")
    config, _ = load_configs()
    analytics = load_analytics(config)

    assert "genai" in analytics
    assert isinstance(analytics["genai"], dict)

    for key, value in analytics["genai"].items():
        # On ignore les métadonnées (ex: description)
        if not isinstance(value, list):
            continue

        for entry in value:
            assert isinstance(entry, dict)
            assert "date" in entry
            assert "count" in entry
            assert isinstance(entry["count"], int)

    print("OK - Analytics valides\n")


def test_traitement():
    print("TEST 3 - Calcul métier (énergie + carbone)")
    results = run_energy_calculation(region="france")

    assert isinstance(results, dict)

    for profile, data in results.items():
        assert "daily" in data
        assert "totals" in data

        totals = data["totals"]
        assert totals["inferences"] > 0
        assert totals["energy_kwh"] > 0
        assert totals["carbon_gco2e"] > 0

    print("OK - Calculs métier corrects\n")


def test_interface():
    print("TEST 4 - Interface Python")
    results = run(region="france")

    assert isinstance(results, dict)

    for profile, data in results.items():
        assert "region" in data
        assert "totals" in data

        totals = data["totals"]
        assert isinstance(totals["inferences"], int)
        assert isinstance(totals["energy_kwh"], float)
        assert isinstance(totals["carbon_gco2e"], float)

    print("OK - Interface fonctionnelle\n")


def run_all_tests():
    print("=" * 50)
    print("LANCEMENT DES TESTS DU PROJET RSE")
    print("=" * 50)

    test_configs()
    test_analytics()
    test_traitement()
    test_interface()

    print("=" * 50)
    print("TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()
