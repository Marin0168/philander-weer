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
    vvn_model = joblib.load("best_vvn_model.pkl")
    vvx_model = joblib.load("best_vvx_model.pkl")
    cloud_base_model = joblib.load("best_wolkenbasis_model.pkl")
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
    """
    for feature in expected_features:
        if feature not in input_data.columns:
            input_data[feature] = 0  # Voeg ontbrekende kolom toe met standaardwaarde
    return input_data[expected_features]

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    location = data.get('location')
    if not location:
        return jsonify({"error": "No location provided"}), 400

    try:
        predictions = predict_weather(location)
        return jsonify(predictions)
    except Exception as e:
        logging.error(f"Voorspelling mislukt: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/route', methods=['POST'])
def calculate_route():
    """
    Bereken modelresultaten voor de route en geef deze terug inclusief kleurcodering.
    """
    route_points = [
        {'name': 'Nordhorn', 'location': '52.4300,7.0700'},
        {'name': 'Oldenzaal', 'location': '52.3000,6.9300'},
        {'name': 'Knooppunt Azelo', 'location': '52.2700,6.6300'},
        {'name': 'Lochem', 'location': '52.1600,6.4200'},
        {'name': 'Valeplas', 'location': '51.9000,5.9000'},
        {'name': 'Waalbrug A50 bij Ewijk', 'location': '51.8600,5.7500'},
        {'name': 'Knooppunt Paalgraven A50 - A59', 'location': '51.7400,5.6000'},
        {'name': 'Den Bosch', 'location': '51.6900,5.3100'},
        {'name': 'Efteling', 'location': '51.6550,5.0460'},
        {'name': 'Keizersveerbrug A27', 'location': '51.7360,4.9010'},
        {'name': 'Moerdijkbrug A16', 'location': '51.7010,4.6320'},
        {'name': 'Haringvlietbrug A29', 'location': '51.7330,4.4160'},
        {'name': 'Grevelingen Dam', 'location': '51.7510,3.8840'},
        {'name': 'Zeeland Brug', 'location': '51.6620,3.8530'},
        {'name': 'Neeltje Jans', 'location': '51.6260,3.7000'},
        {'name': 'Oostkapelle', 'location': '51.5600,3.5500'},
        {'name': 'Oostkapelle-1', 'location': '51.4450,3.5125'},
        {'name': 'Oostkapelle-2', 'location': '51.3300,3.4750'},
        {'name': 'Oostkapelle-3', 'location': '51.2150,3.4375'},
        {'name': 'GILTI', 'location': '51.0900,1.4000'},
        {'name': 'Canterbury', 'location': '51.2800,1.0800'},
        {'name': 'Southend-on-Sea', 'location': '51.5370,0.7130'},
        {'name': 'Witham', 'location': '51.7980,0.6390'},
        {'name': 'Braintree', 'location': '51.8790,0.5510'},
        {'name': 'Duxford', 'location': '52.0900,0.1300'}
    ]

    results = []
    for i in range(len(route_points) - 1):
        start = route_points[i]
        end = route_points[i + 1]

        try:
            prediction = predict_weather(start['location'])
            cloud_base_value = prediction['cloud_base'] * 100

            # Bepaal kleur op basis van cloud_base waarde
            if cloud_base_value < 300:
                color = 'red'
            elif 300 <= cloud_base_value < 600:
                color = 'orange'
            else:
                color = 'green'

            results.append({
                'start': {'name': start['name'], 'location': start['location']},
                'end': {'name': end['name'], 'location': end['location']},
                'VVN': prediction['VVN'],
                'VVX': prediction['VVX'],
                'cloud_base': cloud_base_value,
                'color': color
            })
        except Exception as e:
            results.append({
                'start': {'name': start['name'], 'location': start['location']},
                'end': {'name': end['name'], 'location': end['location']},
                'error': str(e)
            })

    return jsonify(results)

# Main
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
