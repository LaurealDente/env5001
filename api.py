from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional

# Import de VOS classes métier existantes
from traitement import Requete, Modele

app = FastAPI(
    title="GenAI Carbon Calculator (No-YAML)",
    version="3.0.0",
    description="API permettant le calcul dynamique sans dépendance aux fichiers de configuration serveur."
)

# ==========================================
# 1. Modèles de données (Schéma JSON)
# ==========================================

class RegionSpecs(BaseModel):
    pue: float = Field(1.3, description="Power Usage Effectiveness (Efficacité énergétique du datacenter)")
    carbon_intensity: float = Field(60.0, description="Intensité carbone (gCO2e/kWh)")

class HardwareSpecs(BaseModel):
    power_gpu: float = Field(700.0, description="Consommation GPU en Watts")
    power_cpu: float = Field(70.0, description="Consommation CPU en Watts")
    eta_cpu: float = Field(0.15, description="Part d'utilisation du CPU (0.0 à 1.0)")

class UsageProfile(BaseModel):
    name: str = Field("custom_request", description="Nom du profil")
    input_size: int = Field(1000, description="Nombre de tokens/caractères en entrée")
    output_size: int = Field(500, description="Nombre de tokens/caractères en sortie")
    throughput: float = Field(60.0, description="Vitesse de génération (tokens/seconde)")
    count: int = Field(1, description="Nombre d'appels à simuler")

class CalculationRequest(BaseModel):
    region: RegionSpecs
    hardware: HardwareSpecs
    profile: UsageProfile

# ==========================================
# 2. Endpoints
# ==========================================

@app.get("/health")
def health():
    return {"status": "ok", "mode": "dynamic_json"}

@app.post("/calculate-raw")
def calculate_raw(data: CalculationRequest):
    """
    Calcule l'empreinte carbone à partir d'un JSON complet.
    Aucun fichier YAML n'est nécessaire côté serveur.
    """
    try:
        # 1. Instanciation de la Requete (depuis traitement.py)
        req = Requete(name=data.profile.name)
        req.add_topics(data.profile.input_size)
        req.output_size = data.profile.output_size
        
        # 2. Instanciation du Modele (depuis traitement.py)
        # On map les champs du JSON vers les arguments de votre classe
        modele = Modele(
            name=data.profile.name,
            requete=req,
            
            # Contexte Région
            pue=data.region.pue,
            intensite_carbone=data.region.carbon_intensity,
            
            # Contexte Hardware
            power_GPU=data.hardware.power_gpu,
            power_CPU=data.hardware.power_cpu,
            etat_CPU=data.hardware.eta_cpu,
            
            # Performance (Conversion sec -> heures pour votre formule)
            tokens_per_hour=int(data.profile.throughput * 3600),
            
            # Autres défauts
            utilization_rate=1.0 
        )
        
        # 3. Calculs via votre logique quadratique existante
        unit_impact_gco2 = modele.empreinte_requete()
        unit_energy_joules = modele.get_energie_total()
        time_compute = modele.get_t_compute()
        
        # 4. Totaux
        total_co2 = unit_impact_gco2 * data.profile.count
        total_kwh = (unit_energy_joules * data.profile.count) / 3_600_000
        
        return {
            "inputs": {
                "profile": data.profile.name,
                "volume": data.profile.count,
                "region_carbon": data.region.carbon_intensity
            },
            "performance": {
                "time_per_request_sec": round(time_compute, 4),
                "formula_used": "quadratic (input²)"
            },
            "results": {
                "unit_gCO2e": round(unit_impact_gco2, 4),
                "total_gCO2e": round(total_co2, 2),
                "total_kWh": round(total_kwh, 4),
                "total_kgCO2e": round(total_co2 / 1000, 4)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de calcul : {str(e)}")