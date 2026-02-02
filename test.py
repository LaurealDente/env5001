import unittest
import os
from pathlib import Path

# On tente d'importer les classes. Si cela échoue, le test s'arrêtera immédiatement.
try:
    from traitement import Requete, Modele, load_configs, load_analytics_from_disk
except ImportError as e:
    print(f"\nCRITICAL ERROR: Impossible d'importer 'traitement.py'. \nErreur: {e}")
    print("Vérifiez que vous êtes bien à la racine du projet.")
    exit(1)

class TestLogiqueMetier(unittest.TestCase):
    """Teste la logique pure (Classes Requete et Modele) sans fichiers externes"""

    def setUp(self):
        """Initialisation avant chaque test"""
        # On crée une requête standard pour les tests
        self.req = Requete(name="test_unit")
        self.req.add_topics(100)  # Input partie 1
        self.req.add_prompt(200)  # Input partie 2 -> Total Input = 300
        self.req.output_size = 50 # Output = 50

    def test_calcul_taille_entree(self):
        """Vérifie que la somme des inputs est correcte"""
        self.assertEqual(self.req.get_input_size(), 300, "Le calcul de l'input total est faux")

    def test_formule_temps_quadratique(self):
        """
        Vérifie la formule quadratique spécifique demandée :
        T = (Input^2 / Vitesse) + (Output / Vitesse)
        """
        # Hypothèses simples pour calcul mental :
        # Input = 300, Output = 50
        # Vitesse = 3600 tokens/h = 1 token/sec
        tokens_per_hour = 3600 
        
        modele = Modele(
            name="TestModel",
            requete=self.req,
            pue=1.0,
            intensite_carbone=1.0,
            tokens_per_hour=tokens_per_hour # = 1 tok/s
        )
        
        # Calcul attendu :
        # Speed = 1 tok/s
        # T_input = 300^2 / 1 = 90,000 s
        # T_output = 50 / 1 = 50 s
        # Total = 90,050 s
        
        t_compute = modele.get_t_compute()
        self.assertEqual(t_compute, 90050, f"Erreur formule quadratique. Attendu: 90050, Reçu: {t_compute}")

    def test_calcul_energie(self):
        """Vérifie le calcul PUE * (Power * Time)"""
        # On force le temps à 10 secondes pour simplifier ce test (mock)
        # On surcharge la méthode get_t_compute dynamiquement juste pour ce test
        modele = Modele(
            name="TestEnergy",
            requete=self.req,
            pue=1.5,
            intensite_carbone=100, # gCO2/kWh
            power_GPU=100, # Watts
            power_CPU=0,   # On ignore le CPU pour simplifier
            etat_CPU=0.0,  # Donc eta_GPU = 1.0
            utilization_rate=1.0
        )
        
        # On force le temps de calcul à 1h (3600s) pour avoir des kWh ronds
        # 100W * 1h = 100 Wh = 0.1 kWh
        # Total avec PUE 1.5 = 0.15 kWh
        # Carbone = 0.15 * 100 = 15g
        
        # Hack pour le test : on bypass get_t_compute pour valider la suite de la chaine
        modele.get_t_compute = lambda: 3600.0 
        
        resultat_co2 = modele.empreinte_requete()
        
        # 100W * 3600s = 360,000 Joules
        # Energie Total = 360,000 * 1.5 (PUE) = 540,000 J
        # kWh = 540,000 / 3,600,000 = 0.15 kWh
        # CO2 = 0.15 * 100 = 15.0 g
        
        self.assertAlmostEqual(resultat_co2, 15.0, places=2, msg="Le calcul final CO2 est incorrect")


class TestIntegrationFichiers(unittest.TestCase):
    """Teste la lecture des fichiers YAML dans les dossiers config/ et data/"""

    def test_structure_dossiers(self):
        """Vérifie que les fichiers existent aux bons endroits"""
        required_files = [
            "config/config.yaml",
            "config/config_model.yaml",
            "data/2025-FluidTopics-daily-analytics.yaml"
        ]
        for f in required_files:
            self.assertTrue(Path(f).exists(), f"Fichier manquant : {f}")

    def test_chargement_configs(self):
        """Teste la fonction load_configs de traitement.py"""
        try:
            cfg, cfg_model = load_configs()
            
            # Vérification du contenu
            self.assertIn("regions", cfg, "Clé 'regions' manquante dans config.yaml")
            self.assertIn("france", cfg["regions"], "Region 'france' manquante")
            
            self.assertIn("profiles", cfg_model, "Clé 'profiles' manquante dans config_model.yaml")
            self.assertIn("chatbot", cfg_model["profiles"], "Profil 'chatbot' manquant")
            
        except Exception as e:
            self.fail(f"load_configs a levé une exception : {e}")

    def test_chargement_donnees(self):
        """Teste la fonction load_analytics_from_disk"""
        try:
            # On charge d'abord la config pour avoir les chemins
            cfg, _ = load_configs()
            
            # On essaie de charger les données
            data = load_analytics_from_disk(cfg)
            
            self.assertIn("genai", data, "Racine 'genai' manquante dans le fichier analytics")
            self.assertIn("chatbots", data["genai"], "Section 'chatbots' manquante")
            self.assertIsInstance(data["genai"]["chatbots"], list, "Les données chatbots devraient être une liste")
            
        except Exception as e:
            self.fail(f"Le chargement des analytics a échoué : {e}")

if __name__ == '__main__':
    print("========================================")
    print("DEMARRAGE DU TEST DE TRAITEMENT.PY")
    print("========================================")
    unittest.main(verbosity=2)