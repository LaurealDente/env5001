import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

class Requete :
    def __init__(self, name):
        self.name = name
        self.output_size = 0
        self.topics = []
        self.prompts = []

    def get_input_size(self):
        return self.get_total_topics_size() + self.get_total_prompts_size()

    def get_total_topics_size(self) :
        return sum(self.topics)
    
    def get_total_prompts_size(self):
        return  sum(self.prompts)
    
    def add_prompt(self, size:int):
        self.prompts.append(size)

    def add_topics(self, size:int):
        self.topics.append(size)
    
    def get_output_size(self):
        return self.output_size
    
    def nb_tokens(self):
        if self.name == "translation":
            return 0.5*self.get_total_topics_size()
        return (self.get_input_size()+self.get_output_size())/4


class Modele :
    def __init__(self, name:str, requete:Requete, pue:float, intensite_carbone:float, utilization_rate:float = 1, etat_CPU:float=0.3, power_CPU:float=85, power_GPU:float=700, tokens_per_hour:int=216000):
        self.name = name

        # Infrastructure
        self.pue = pue
        self.utilization_rate = utilization_rate

        # Serveurs
        self.eta_CPU = etat_CPU
        self.eta_GPU = 1.0 - self.eta_CPU

        # Caractéristiques fournisseurs
        self.power_CPU = power_CPU
        self.power_GPU = power_GPU
        self.tokens_per_hour = tokens_per_hour

        # Requête
        self.requete = requete

        # Pays
        self.intensite_carbone = intensite_carbone
    
    def get_t_compute(self):
        ## Erreur de calcul dans la méthodologie proposée
        ## Cette formule quadratique sur les tokens d'entrées doivent être considérés comme parallélisé dans la GPU conseil pour la suite :
        # return (self.requete.get_input_size() / 100.0 + self.requete.get_output_size()) / (self.tokens_per_hour / 3600.0)
        return (self.requete.get_input_size()*self.requete.get_input_size())/(self.tokens_per_hour/3600) + self.requete.get_output_size()/(self.tokens_per_hour/3600)

    def get_energie_inference(self):
        return self.power_GPU * self.eta_GPU * self.get_t_compute() + self.power_CPU * self.eta_CPU * self.get_t_compute()
    
    def get_energie_infrastructure(self) :
        return self.pue * self.utilization_rate
    
    def get_energie_total(self):
        return self.get_energie_inference()*self.get_energie_infrastructure()

    def empreinte_requete(self):
        return (self.get_energie_total()/3600000)*self.intensite_carbone



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

