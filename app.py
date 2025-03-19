import os
import logging
import joblib
import requests
import pandas as pd
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Instellingen en configuraties
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# API-configuratie
API_KEY = os.getenv("WEATHER_API_KEY", "8a373f54eb")
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
            input_data[feature] = 0  # Voeg ontbrekende kolom toe met standaardwaarde
    return input_data[expected_features]

# Functies (ongewijzigd)
def get_expected_features(model):
    return getattr(model, 'feature_names_in_', None)

def synchronize_features(input_data, expected_features):
    for feature in expected_features:
        if feature not in input_data.columns:
            input_data[feature] = 0
    return input_data[expected_features]

def fetch_real_time_weather(location):
    params = {"key": API_KEY, "locatie": location}
    response = requests.get(BASE_WEATHER_URL, params=params)
    if response.status_code == 200:
        data = response.json().get('liveweer', [])[0]
        weather_data = {
            'RH': float(data.get('neerslag', 0.0)),
            'PG': float(data.get('luchtd', 0.0)),
            'FHN': float(data.get('windsnelheid', 0.0)),
            'FXX': float(data.get('windstoten', 0.0)),
            'DDVEC': float(data.get('windrgr', 0.0)),
            'Q': float(data.get('zon', 0.0)),
            'UX': float(data.get('lv', 0.0)),
            'TN': float(data.get('temp', 0.0)),
            'TG': float(data.get('temp24', 0.0)),
            'temperature_2m': float(data.get('temp', 0.0)),
            'relative_humidity_2m': float(data.get('lv', 0.0)),
            'wind_speed_10m': float(data.get('windsnelheid', 0.0)),
            'wind_direction_10m': float(data.get('windrgr', 0.0)),
            'dew_point': float(data.get('dauwp', 0.0)),
            'temperature_diff': 0.0,
            'humidity_diff': 0.0,
            'turbulence': 0.0,
            'month': pd.Timestamp.now().month,
        }
        weather_data['season'] = pd.Series(weather_data['month']).map({
            12: 'winter', 1: 'winter', 2: 'winter',
            3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer',
            9: 'autumn', 10: 'autumn', 11: 'autumn'
        }).iloc[0]
        weather_df = pd.DataFrame([weather_data])
        weather_df = pd.get_dummies(weather_df, columns=['season'], drop_first=True)
        for season in ['season_spring', 'season_summer', 'season_autumn']:
            if season not in weather_df.columns:
                weather_df[season] = 0
        return weather_df.iloc[0].to_dict()
    else:
        raise Exception(f"Fout bij het ophalen van weerdata: {response.status_code}")

def predict_weather(location):
    real_time_data = fetch_real_time_weather(location)
    input_data = pd.DataFrame([real_time_data])
    vvn_input = synchronize_features(input_data, get_expected_features(vvn_model))
    vvx_input = synchronize_features(input_data, get_expected_features(vvx_model))
    cloud_base_input = synchronize_features(input_data, get_expected_features(cloud_base_model))
    return {
        "VVN": vvn_model.predict(vvn_input)[0],
        "VVX": vvx_model.predict(vvx_input)[0],
        "cloud_base": cloud_base_model.predict(cloud_base_input)[0]
    }

# Routes (inclusief route-definitie)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    location = data.get('location')
    if not location:
        return jsonify({"error": "No location provided"}), 400
    predictions = predict_weather(location)
    return jsonify(predictions)

@app.route('/route', methods=['POST'])
def calculate_route():
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
        prediction = predict_weather(start['location'])
        cloud_base_value = prediction['cloud_base'] * 100
        color = 'green' if cloud_base_value >= 600 else 'orange' if cloud_base_value >= 300 else 'red'
        results.append({
            'start': start,
            'end': end,
            'VVN': prediction['VVN'],
            'VVX': prediction['VVX'],
            'cloud_base': cloud_base_value,
            'color': color
        })
    return jsonify(results)

# -------------------------------
# Nieuwe route voor privacy.html
# -------------------------------
@app.route('/privacybeleid')
def privacy():
    """
    Deze route toont de privacyverklaring via het template privacy.html.
    Zorg ervoor dat 'templates/privacy.html' aanwezig is met de juiste inhoud.
    """
    return render_template('privacybeleid.html')

@app.route('/google')
def google():
    """
    Deze route verwerkt de POST-aanvraag van de privacyverklaring.
    Voer hier de logica uit om de acceptatie van de privacyverklaring op te slaan.
    """
    return render_template('google3000da14148dd0e4.html')


# Main
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
