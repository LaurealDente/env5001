#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
traitement.py — Métier (calculs + parsing)

Implémente la méthodologie fournie dans les documents :
- Conversion caractères -> tokens : 1 token ~= 4 caractères
- Profils : TRANSLATION, COMPLETION, CHATBOT
- Énergie (formules simplifiées issues de la méthodologie fusionnée)

Unités :
- Les formules d'énergie ci-dessous renvoient une énergie en **Joules** (J).
- Conversion : 1 kWh = 3.6e6 J
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import datetime as _dt

import yaml


KWH_PER_J = 1.0 / 3_600_000.0


# -----------------------------
# Config
# -----------------------------

@dataclass(frozen=True)
class SimulationParams:
    # tailles (en caractères)
    topic_size_chars: int = 2000
    prompt_size_chars: int = 400

    # chatbot : nombre moyen de topics et nombre de prompts (turns) par conversation
    chatbot_avg_topics: int = 10
    chatbot_avg_prompts: int = 2

    # sortie moyenne en tokens pour completion/chatbot (méthodo ~300 tokens)
    output_tokens_avg: int = 300


@dataclass(frozen=True)
class CarbonParams:
    # gCO2e / kWh
    carbon_intensity_g_per_kwh: float = 250.0


@dataclass(frozen=True)
class PathsConfig:
    analytics_yaml: Path


@dataclass(frozen=True)
class Config:
    paths: PathsConfig
    simulation: SimulationParams
    carbon: CarbonParams


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(config_path: Path, repo_root: Path) -> Config:
    """
    Charge config/config.yaml.
    Toutes les valeurs ont des défauts raisonnables si absentes.
    """
    raw = load_yaml(config_path) if config_path.exists() else {}

    # paths
    analytics_rel = raw.get("paths", {}).get("analytics_yaml", "data/2025-FluidTopics-daily-analytics.yaml")
    analytics_path = (repo_root / analytics_rel).resolve()

    # simulation
    sim = raw.get("simulation", {})
    simulation = SimulationParams(
        topic_size_chars=int(sim.get("topic_size_chars", 2000)),
        prompt_size_chars=int(sim.get("prompt_size_chars", 400)),
        chatbot_avg_topics=int(sim.get("chatbot_avg_topics", 10)),
        chatbot_avg_prompts=int(sim.get("chatbot_avg_prompts", 2)),
        output_tokens_avg=int(sim.get("output_tokens_avg", 300)),
    )

    # carbon
    carb = raw.get("carbon", {})
    carbon = CarbonParams(
        carbon_intensity_g_per_kwh=float(carb.get("carbon_intensity_g_per_kwh", 250.0))
    )

    return Config(
        paths=PathsConfig(analytics_yaml=analytics_path),
        simulation=simulation,
        carbon=carbon,
    )


# -----------------------------
# Parsing analytics
# -----------------------------

def _parse_date(d: str) -> _dt.date:
    return _dt.date.fromisoformat(d)


def parse_daily_counts(analytics_yaml_path: Path) -> Dict[_dt.date, Dict[str, int]]:
    """
    Lit le YAML analytics Fluid Topics et renvoie, pour chaque date :
    { "chatbots": int, "completions": int, "translations": int, "sessions": int (si présent) }
    """
    raw = load_yaml(analytics_yaml_path)

    # genai profiles
    genai = raw.get("genai", {})
    out: Dict[_dt.date, Dict[str, int]] = {}

    def ingest(profile_key: str, target_key: str):
        for item in genai.get(profile_key, []) or []:
            date = _parse_date(item["date"])
            out.setdefault(date, {}).setdefault(target_key, 0)
            out[date][target_key] += int(item.get("count", 0))

    ingest("chatbots", "chatbots")
    ingest("completions", "completions")
    ingest("translations", "translations")

    # sessions (optionnel)
    session = raw.get("session", {})
    sessions_list = session.get("sessions", []) or []
    for item in sessions_list:
        date = _parse_date(item["date"])
        out.setdefault(date, {}).setdefault("sessions", 0)
        out[date]["sessions"] += int(item.get("count", 0))

    # ensure keys exist
    for date in list(out.keys()):
        out[date].setdefault("chatbots", 0)
        out[date].setdefault("completions", 0)
        out[date].setdefault("translations", 0)
        out[date].setdefault("sessions", 0)

    return dict(sorted(out.items(), key=lambda x: x[0]))


# -----------------------------
# Tokens (méthodologie)
# -----------------------------

def chars_to_tokens(chars: int) -> float:
    # 1 token ~= 4 chars
    return chars / 4.0


def tokens_for_translation(sim: SimulationParams) -> Tuple[float, float]:
    tokens_in = chars_to_tokens(sim.topic_size_chars)
    tokens_out = chars_to_tokens(sim.topic_size_chars)
    return tokens_in, tokens_out


def tokens_for_completion(sim: SimulationParams) -> Tuple[float, float]:
    tokens_in = chars_to_tokens(sim.topic_size_chars + sim.prompt_size_chars)
    tokens_out = float(sim.output_tokens_avg)
    return tokens_in, tokens_out


def tokens_for_chatbot(sim: SimulationParams) -> Tuple[float, float]:
    tokens_in = chars_to_tokens(sim.chatbot_avg_topics * sim.topic_size_chars + sim.chatbot_avg_prompts * sim.prompt_size_chars)
    tokens_out = float(sim.output_tokens_avg)
    return tokens_in, tokens_out


# -----------------------------
# Énergie (formules méthodologie fusionnée)
# -----------------------------
# NB: les équations ci-dessous sont les formes "simplifiées" fournies dans la méthodologie.
# Elles sont exprimées en Joules (J). On convertit ensuite en kWh.

def energy_j_translation(tokens_in: float, tokens_out: float) -> float:
    # E_translation = (input_tokens^2 + output_tokens) * 10.7645
    return (tokens_in ** 2 + tokens_out) * 10.7645


def energy_j_completion(tokens_in: float, tokens_out: float) -> float:
    # Forme simplifiée vue dans la méthodologie fusionnée :
    # E_completion = (input_tokens^2)/60 + 3650.5625
    # tokens_out est déjà "absorbé" dans la constante (moyenne ~300 tokens).
    # On garde tokens_out en param pour compatibilité / évolutions.
    return (tokens_in ** 2) / 60.0 + 3650.5625


def energy_j_chatbot(tokens_in: float, tokens_out: float) -> float:
    # E_chatbot = (input_tokens^2)/60 + 3650.5625
    return (tokens_in ** 2) / 60.0 + 3650.5625


# -----------------------------
# Calculs journaliers + agrégation
# -----------------------------

def _profile_metrics(profile: str, count: int, sim: SimulationParams, carbon: CarbonParams) -> Dict[str, float]:
    """
    Retourne metrics pour un profil sur une journée.
    """
    if profile == "translation":
        tin, tout = tokens_for_translation(sim)
        e_j = energy_j_translation(tin, tout)
    elif profile == "completion":
        tin, tout = tokens_for_completion(sim)
        e_j = energy_j_completion(tin, tout)
    elif profile == "chatbot":
        tin, tout = tokens_for_chatbot(sim)
        e_j = energy_j_chatbot(tin, tout)
    else:
        raise ValueError(f"Profil inconnu: {profile}")

    tokens_total = (tin + tout) * count
    energy_j_total = e_j * count
    energy_kwh_total = energy_j_total * KWH_PER_J
    co2_g_total = energy_kwh_total * carbon.carbon_intensity_g_per_kwh

    return {
        "count": float(count),
        "tokens_in_per_call": float(tin),
        "tokens_out_per_call": float(tout),
        "tokens_total": float(tokens_total),
        "energy_j_per_call": float(e_j),
        "energy_j_total": float(energy_j_total),
        "energy_kwh_total": float(energy_kwh_total),
        "co2_g_total": float(co2_g_total),
    }


def compute_daily(config: Config) -> Dict[str, Any]:
    """
    Calcule les métriques pour toutes les dates présentes dans le YAML analytics.
    """
    daily_counts = parse_daily_counts(config.paths.analytics_yaml)

    results: Dict[str, Any] = {"days": []}

    for date, counts in daily_counts.items():
        trans = _profile_metrics("translation", counts["translations"], config.simulation, config.carbon)
        comp = _profile_metrics("completion", counts["completions"], config.simulation, config.carbon)
        chat = _profile_metrics("chatbot", counts["chatbots"], config.simulation, config.carbon)

        totals = {
            "tokens_total": trans["tokens_total"] + comp["tokens_total"] + chat["tokens_total"],
            "energy_j_total": trans["energy_j_total"] + comp["energy_j_total"] + chat["energy_j_total"],
            "energy_kwh_total": trans["energy_kwh_total"] + comp["energy_kwh_total"] + chat["energy_kwh_total"],
            "co2_g_total": trans["co2_g_total"] + comp["co2_g_total"] + chat["co2_g_total"],
        }

        results["days"].append({
            "date": date.isoformat(),
            "sessions": int(counts.get("sessions", 0)),
            "profiles": {
                "translation": trans,
                "completion": comp,
                "chatbot": chat,
            },
            "totals": totals
        })

    return results


def compute_summary(results: Dict[str, Any]) -> Dict[str, float]:
    """
    Agrège sur toute la période.
    """
    tokens = 0.0
    energy_j = 0.0
    energy_kwh = 0.0
    co2_g = 0.0
    for day in results.get("days", []):
        t = day["totals"]
        tokens += t["tokens_total"]
        energy_j += t["energy_j_total"]
        energy_kwh += t["energy_kwh_total"]
        co2_g += t["co2_g_total"]

    return {
        "tokens_total": tokens,
        "energy_j_total": energy_j,
        "energy_kwh_total": energy_kwh,
        "co2_g_total": co2_g,
    }


def filter_range(results: Dict[str, Any], start: Optional[str] = None, end: Optional[str] = None) -> Dict[str, Any]:
    """
    Filtre les jours dans [start, end] inclus.
    """
    days = results.get("days", [])
    if start:
        s = _dt.date.fromisoformat(start)
        days = [d for d in days if _dt.date.fromisoformat(d["date"]) >= s]
    if end:
        e = _dt.date.fromisoformat(end)
        days = [d for d in days if _dt.date.fromisoformat(d["date"]) <= e]
    return {"days": days}
