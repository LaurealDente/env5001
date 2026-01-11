from fastapi import FastAPI, Query
from interface import run

app = FastAPI(
    title="Energy & Carbon Calculator API",
    description="API de calcul de consommation énergétique et carbone (gCO₂e)",
    version="1.0"
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/energy")
def compute_energy(
    region: str = Query(default=None, description="Région de calcul (france, usa, germany, iceland)")
):
    return run(region=region)
