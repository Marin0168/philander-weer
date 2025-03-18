import os
import logging
import joblib
import requests
import pandas as pd
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Instellingen en configuraties
app = Flask(__name__)
CORS(app)  # Cross-Origin Resource Sharing support
logging.basicConfig(level=logging.INFO)

# API-configuratie
API_KEY = os.getenv("WEATHER_API_KEY", "8a373f54eb")  # Gebruik environment variabelen
BASE_WEATHER_URL = "https://weerlive.nl/api/weerlive_api_v2.php"

# Laad de modellen met foutafhandeling
try:
    vvn_model = joblib.load("models/best_vvn_model.pkl")
    vvx_model = joblib.load("models/best_vvx_model.pkl")
    cloud_base_model = joblib.load("models/best_wolkenbasis_model.pkl")
except FileNotFoundError as e:
    logging.error("Modelbestanden niet gevonden! Zorg ervoor dat de modelbestanden bestaan.")
    raise SystemExit("Fout: Modelbestanden niet geladen.") from e

def get_expected_features(model):
    """
    Haalt de verwachte feature-namen op van een model.
    """
    return getattr(model, 'feature_names_in_', None)

def synchronize_features(input_data, expected_features):
    """
    Synchroniseert de input DataFrame met de verwachte features.
    - Voegt ontbrekende kolommen toe met standaardwaarden.
    - Zorgt voor de juiste volgorde van de kolommen.
    """
    for feature in expected_features:
        if feature not in input_data.columns:
            input_
