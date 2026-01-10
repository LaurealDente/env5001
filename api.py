#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api.py — Contrôleur (interface publique)

API FastAPI :
- /health
- /summary
- /daily/{date}
- /range?start=YYYY-MM-DD&end=YYYY-MM-DD
+ /ui (petit dashboard élégant)
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from traitement import load_config, compute_daily, compute_summary, filter_range

APP_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = APP_ROOT / "config" / "config.yaml"

app = FastAPI(title="ENV5001 – Energy Estimator", version="1.1.0")


# -----------------------------
# API endpoints (inchangés)
# -----------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/summary")
def summary():
    cfg = load_config(CONFIG_PATH, APP_ROOT)
    results = compute_daily(cfg)
    return {
        "config": {
            "topic_size_chars": cfg.simulation.topic_size_chars,
            "prompt_size_chars": cfg.simulation.prompt_size_chars,
            "chatbot_avg_topics": cfg.simulation.chatbot_avg_topics,
            "chatbot_avg_prompts": cfg.simulation.chatbot_avg_prompts,
            "output_tokens_avg": cfg.simulation.output_tokens_avg,
            "carbon_intensity_g_per_kwh": cfg.carbon.carbon_intensity_g_per_kwh,
            "analytics_yaml": str(cfg.paths.analytics_yaml),
        },
        "summary": compute_summary(results),
    }


@app.get("/daily/{date}")
def daily(date: str):
    cfg = load_config(CONFIG_PATH, APP_ROOT)
    results = compute_daily(cfg)

    for day in results["days"]:
        if day["date"] == date:
            return day

    raise HTTPException(status_code=404, detail=f"Date inconnue: {date}")


@app.get("/range")
def range_endpoint(
    start: str | None = Query(default=None, description="YYYY-MM-DD"),
    end: str | None = Query(default=None, description="YYYY-MM-DD"),
):
    cfg = load_config(CONFIG_PATH, APP_ROOT)
    results = compute_daily(cfg)
    filtered = filter_range(results, start=start, end=end)
    return {
        "range": {"start": start, "end": end},
        "summary": compute_summary(filtered),
        "days": filtered["days"],
    }


# -----------------------------
# UI (amélioration rapide)
# -----------------------------

@app.get("/", include_in_schema=False)
def root():
    # Petit confort : ouvrir directement l’UI
    return RedirectResponse(url="/ui")


@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def ui():
    # UI 100% statique (HTML+JS) qui consomme /range
    # -> aucune dépendance front à installer
    return HTMLResponse(
        """
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ENV5001 – Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root{
      --bg: #0b1020;
      --card: rgba(255,255,255,.06);
      --card2: rgba(255,255,255,.08);
      --text: rgba(255,255,255,.92);
      --muted: rgba(255,255,255,.65);
      --line: rgba(255,255,255,.12);
      --shadow: 0 10px 30px rgba(0,0,0,.35);
      --radius: 16px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; padding: 22px;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
      background: radial-gradient(1200px 700px at 10% 10%, rgba(99,102,241,.35), transparent 60%),
                  radial-gradient(900px 600px at 80% 30%, rgba(16,185,129,.22), transparent 55%),
                  var(--bg);
      color: var(--text);
    }
    .container { max-width: 1100px; margin: 0 auto; }
    .header {
      display:flex; justify-content:space-between; align-items:flex-end;
      gap: 12px; margin-bottom: 16px;
    }
    h1 { font-size: 22px; margin: 0; letter-spacing: .2px; }
    .sub { color: var(--muted); font-size: 13px; margin-top: 6px; }
    .pill {
      display:inline-flex; gap:8px; align-items:center;
      padding: 8px 10px; border:1px solid var(--line);
      background: rgba(255,255,255,.04); border-radius: 999px;
      color: var(--muted); font-size: 12px;
    }

    .panel {
      border: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(255,255,255,.07), rgba(255,255,255,.04));
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 14px;
    }

    .controls {
      display:flex; flex-wrap:wrap; gap:10px; align-items:end;
      margin-bottom: 12px;
    }
    label { display:flex; flex-direction:column; gap:6px; font-size:12px; color: var(--muted); }
    input[type="date"]{
      padding: 8px 10px; border-radius: 12px; border:1px solid var(--line);
      background: rgba(255,255,255,.06); color: var(--text);
      outline: none;
    }
    button {
      padding: 9px 12px; border-radius: 12px; border:1px solid var(--line);
      background: rgba(255,255,255,.08);
      color: var(--text);
      cursor: pointer;
      transition: transform .06s ease, background .15s ease;
    }
    button:hover { background: rgba(255,255,255,.12); }
    button:active { transform: translateY(1px); }

    .grid {
      display:grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-top: 10px;
    }
    @media (max-width: 980px){
      .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 520px){
      .grid { grid-template-columns: 1fr; }
    }
    .card {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.06);
      border-radius: var(--radius);
      padding: 12px;
    }
    .kpiTitle { color: var(--muted); font-size: 12px; }
    .kpiValue { font-size: 22px; font-weight: 750; margin-top: 6px; }
    .kpiHint  { color: var(--muted); font-size: 12px; margin-top: 6px; }

    .split {
      display:grid;
      grid-template-columns: 1.4fr .6fr;
      gap: 10px;
      margin-top: 10px;
    }
    @media (max-width: 980px){
      .split { grid-template-columns: 1fr; }
    }

    .tableWrap { overflow:auto; border-radius: var(--radius); border:1px solid var(--line); }
    table {
      width:100%;
      border-collapse: collapse;
      font-size: 13px;
      background: rgba(255,255,255,.04);
    }
    th, td { padding: 10px 10px; border-bottom: 1px solid var(--line); }
    th { text-align:left; color: var(--muted); font-weight: 600; background: rgba(255,255,255,.05); }
    tr:hover td { background: rgba(255,255,255,.04); }
    .right { text-align:right; }

    .msg { color: var(--muted); font-size: 13px; margin-top: 6px; }
    pre {
      margin: 0;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255,255,255,.04);
      color: rgba(255,255,255,.8);
      overflow:auto;
      font-size: 12px;
      max-height: 310px;
    }
    .row2 { display:flex; gap: 10px; flex-wrap:wrap; justify-content:space-between; align-items:center; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1>ENV5001 — Estimation Tokens / Énergie / CO₂</h1>
        <div class="sub">Dashboard léger branché sur <span class="pill">/range</span> (aucun build front)</div>
      </div>
      <div class="pill" id="status">⏳ prêt</div>
    </div>

    <div class="panel">
      <div class="controls">
        <label>
          Date début
          <input id="start" type="date" />
        </label>
        <label>
          Date fin
          <input id="end" type="date" />
        </label>
        <button id="btnLoad">Charger</button>
        <button id="btnCopy">Copier résumé</button>
        <button id="btnJson">Exporter JSON</button>
      </div>

      <div class="grid">
        <div class="card">
          <div class="kpiTitle">Tokens (total)</div>
          <div class="kpiValue" id="kpiTokens">—</div>
          <div class="kpiHint">Σ sur la période</div>
        </div>
        <div class="card">
          <div class="kpiTitle">Énergie (kWh)</div>
          <div class="kpiValue" id="kpiEnergy">—</div>
          <div class="kpiHint">Σ sur la période</div>
        </div>
        <div class="card">
          <div class="kpiTitle">CO₂ (kg)</div>
          <div class="kpiValue" id="kpiCo2">—</div>
          <div class="kpiHint">Σ sur la période</div>
        </div>
        <div class="card">
          <div class="kpiTitle">Jours</div>
          <div class="kpiValue" id="kpiDays">—</div>
          <div class="kpiHint">Nombre de points</div>
        </div>
      </div>

      <div class="split">
        <div class="card">
          <div class="row2">
            <div class="kpiTitle">Évolution journalière</div>
            <div class="kpiHint msg">Survol = détails</div>
          </div>
          <canvas id="chart" height="120"></canvas>
        </div>

        <div class="card">
          <div class="kpiTitle">Dernier JSON</div>
          <div class="msg">Pratique pour copier/coller dans ton rapport.</div>
          <pre id="raw">—</pre>
        </div>
      </div>

      <div style="margin-top: 10px;" class="card">
        <div class="kpiTitle">Détail par jour</div>
        <div class="msg">Clique “Charger” après avoir choisi la période.</div>
        <div class="tableWrap" style="margin-top: 10px;">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th class="right">Tokens</th>
                <th class="right">Énergie (kWh)</th>
                <th class="right">CO₂ (kg)</th>
              </tr>
            </thead>
            <tbody id="tbody">
              <tr><td colspan="4" class="msg">—</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="msg" style="margin-top: 10px;">
        Tip: endpoints API → <span class="pill">/docs</span> • <span class="pill">/summary</span> • <span class="pill">/range</span>
      </div>
    </div>
  </div>

<script>
  const statusEl = document.getElementById("status");
  const setStatus = (txt) => statusEl.textContent = txt;

  const fmtInt = (x) => (x ?? 0).toLocaleString("fr-FR");
  const fmt2 = (x) => (x ?? 0).toLocaleString("fr-FR", { maximumFractionDigits: 2 });

  // Selon ta sortie compute_summary / compute_daily, ces clés peuvent varier.
  // On “normalise” pour que l’UI reste robuste.
  function pick(obj, keys, fallback=0){
    for (const k of keys){
      if (obj && obj[k] !== undefined && obj[k] !== null) return obj[k];
    }
    return fallback;
  }

  function normalizeSummary(obj){
    return {
      tokens: pick(obj, ["tokens_total","tokens","total_tokens"]),
      energy: pick(obj, ["energy_kwh_total","energy_kwh","energy"]),
      co2: pick(obj, ["co2_kg_total","co2_kg","co2"]),
    };
  }

  function normalizeDay(d){
    return {
      date: pick(d, ["date","day"], ""),
      tokens: pick(d, ["tokens_total","tokens","total_tokens"]),
      energy: pick(d, ["energy_kwh_total","energy_kwh","energy"]),
      co2: pick(d, ["co2_kg_total","co2_kg","co2"]),
    };
  }

  let chart;
  function renderChart(points){
    const labels = points.map(p => p.date);
    const tokens = points.map(p => p.tokens);
    const energy = points.map(p => p.energy);
    const co2 = points.map(p => p.co2);

    const ctx = document.getElementById("chart").getContext("2d");
    if (chart) chart.destroy();

    chart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          { label: "Tokens", data: tokens, yAxisID: "yTokens", tension: 0.25 },
          { label: "Énergie (kWh)", data: energy, yAxisID: "yEnergy", tension: 0.25 },
          { label: "CO₂ (kg)", data: co2, yAxisID: "yCo2", tension: 0.25 },
        ]
      },
      options: {
        responsive: true,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { labels: { color: "rgba(255,255,255,.8)" } },
          tooltip: { enabled: true }
        },
        scales: {
          x: { ticks: { color: "rgba(255,255,255,.65)" }, grid: { color: "rgba(255,255,255,.08)" } },
          yTokens: { position: "left", ticks:{ color:"rgba(255,255,255,.65)" }, grid:{ color:"rgba(255,255,255,.08)" } },
          yEnergy: { position: "right", grid: { drawOnChartArea: false }, ticks:{ color:"rgba(255,255,255,.65)" } },
          yCo2:   { position: "right", grid: { drawOnChartArea: false }, ticks:{ color:"rgba(255,255,255,.65)" } }
        }
      }
    });
  }

  function renderTable(points){
    const tbody = document.getElementById("tbody");
    if (!points.length){
      tbody.innerHTML = `<tr><td colspan="4" class="msg">Aucune donnée sur la période.</td></tr>`;
      return;
    }
    tbody.innerHTML = points.map(p => `
      <tr>
        <td>${p.date}</td>
        <td class="right">${fmtInt(p.tokens)}</td>
        <td class="right">${fmt2(p.energy)}</td>
        <td class="right">${fmt2(p.co2)}</td>
      </tr>
    `).join("");
  }

  async function loadData(){
    const start = document.getElementById("start").value;
    const end = document.getElementById("end").value;

    if (!start || !end){
      alert("Choisis une date début et fin.");
      return;
    }

    setStatus("⏳ chargement…");
    try{
      const r = await fetch(`/range?start=${start}&end=${end}`);
      if (!r.ok) throw new Error("Erreur API /range");
      const data = await r.json();

      const sum = normalizeSummary(data.summary || data);
      const days = Array.isArray(data.days) ? data.days.map(normalizeDay) : [];

      document.getElementById("kpiTokens").textContent = fmtInt(sum.tokens);
      document.getElementById("kpiEnergy").textContent = fmt2(sum.energy);
      document.getElementById("kpiCo2").textContent = fmt2(sum.co2);
      document.getElementById("kpiDays").textContent = fmtInt(days.length);

      document.getElementById("raw").textContent = JSON.stringify(data, null, 2);

      if (days.length) renderChart(days);
      renderTable(days);

      setStatus("✅ OK");
    } catch(e){
      console.error(e);
      setStatus("❌ erreur");
      alert("Impossible de charger les données. Vérifie que l'API /range fonctionne.");
    }
  }

  document.getElementById("btnLoad").addEventListener("click", loadData);

  document.getElementById("btnCopy").addEventListener("click", async () => {
    const tokens = document.getElementById("kpiTokens").textContent;
    const energy = document.getElementById("kpiEnergy").textContent;
    const co2 = document.getElementById("kpiCo2").textContent;
    const start = document.getElementById("start").value;
    const end = document.getElementById("end").value;

    const text = `Période ${start} → ${end} | Tokens: ${tokens} | Énergie: ${energy} kWh | CO₂: ${co2} kg`;
    await navigator.clipboard.writeText(text);
    alert("Résumé copié !");
  });

  document.getElementById("btnJson").addEventListener("click", () => {
    const blob = new Blob([document.getElementById("raw").textContent], {type: "application/json"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "resultats.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });

  // Petit preset dates (si tu veux)
  // -> par défaut, met aujourd'hui / aujourd'hui, mais tu peux choisir toi-même.
  // Ici on met la date du jour dans les inputs si vides.
  (function init(){
    const s = document.getElementById("start");
    const e = document.getElementById("end");
    if (!s.value || !e.value){
      const now = new Date();
      const yyyy = now.getFullYear();
      const mm = String(now.getMonth()+1).padStart(2,'0');
      const dd = String(now.getDate()).padStart(2,'0');
      const today = `${yyyy}-${mm}-${dd}`;
      s.value = today;
      e.value = today;
    }
  })();
</script>

</body>
</html>
"""
    )
