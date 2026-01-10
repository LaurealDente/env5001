#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
interface.py — Vue (formatage résultats)

Usage :
    python interface.py summary
    python interface.py daily 2025-08-12
    python interface.py range 2025-08-12 2025-08-31
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from traitement import load_config, compute_daily, compute_summary, filter_range

APP_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = APP_ROOT / "config" / "config.yaml"


def _print(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1

    cmd = argv[1].lower()
    cfg = load_config(CONFIG_PATH, APP_ROOT)
    results = compute_daily(cfg)

    if cmd == "summary":
        _print({
            "summary": compute_summary(results),
            "config": {
                "topic_size_chars": cfg.simulation.topic_size_chars,
                "prompt_size_chars": cfg.simulation.prompt_size_chars,
                "chatbot_avg_topics": cfg.simulation.chatbot_avg_topics,
                "chatbot_avg_prompts": cfg.simulation.chatbot_avg_prompts,
                "output_tokens_avg": cfg.simulation.output_tokens_avg,
                "carbon_intensity_g_per_kwh": cfg.carbon.carbon_intensity_g_per_kwh,
            }
        })
        return 0

    if cmd == "daily":
        if len(argv) != 3:
            print("Usage: python interface.py daily YYYY-MM-DD")
            return 1
        date = argv[2]
        day = next((d for d in results["days"] if d["date"] == date), None)
        if not day:
            print(f"Date inconnue: {date}")
            return 2
        _print(day)
        return 0

    if cmd == "range":
        if len(argv) != 4:
            print("Usage: python interface.py range START END")
            return 1
        start, end = argv[2], argv[3]
        filtered = filter_range(results, start=start, end=end)
        _print({
            "range": {"start": start, "end": end},
            "summary": compute_summary(filtered),
            "days": filtered["days"],
        })
        return 0

    print(f"Commande inconnue: {cmd}")
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
