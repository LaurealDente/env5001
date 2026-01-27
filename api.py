from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from traitement import run_energy_calculation_from_yaml_text
from interface import format_results  # si tu as bien cette fonction

app = FastAPI(
    title="ENV5001 Energy & Carbon API",
    version="1.0.0",
    description="Calcule énergie (kWh) et carbone (gCO2e) à partir d'un fichier analytics YAML envoyé dans la requête."
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/energy")
async def energy(
    region: str = Query(default=None, description="Région (france, usa, germany, iceland, etc.)"),
    analytics_file: UploadFile = File(..., description="Fichier YAML analytics")
):
    # Vérif extension
    name = (analytics_file.filename or "").lower()
    if not name.endswith((".yml", ".yaml")):
        raise HTTPException(status_code=400, detail="Le fichier doit être un YAML (.yml/.yaml).")

    # Lire contenu
    raw = await analytics_file.read()
    yaml_text = raw.decode("utf-8", errors="replace")

    try:
        raw_results = run_energy_calculation_from_yaml_text(yaml_text, region=region)
        pretty = format_results(raw_results)
        return {"region": region, "results": pretty}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
