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
            input_data[feature] = 0  # Voeg ontbrekende kolom toe met standaardwaarde
    return input_data[expected_features]


# Functies
def fetch_real_time_weather(location):
    """
    Haalt real-time weerdata op voor een opgegeven locatie en voegt samengestelde features toe.
    """
    params = {"key": API_KEY, "locatie": location}
    response = requests.get(BASE_WEATHER_URL, params=params)
    if response.status_code == 200:
        try:
            data = response.json().get('liveweer', [])[0]
            
            # Basisgegevens uit API
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
                'temperature_diff': 0.0,  # Placeholder voor enkel datapunt
                'humidity_diff': 0.0,  # Placeholder
                'turbulence': 0.0,  # Placeholder
                'month': pd.Timestamp.now().month,
            }

            # Voeg seizoensinformatie toe
            weather_data['season'] = pd.Series(weather_data['month']).map({
                12: 'winter', 1: 'winter', 2: 'winter',
                3: 'spring', 4: 'spring', 5: 'spring',
                6: 'summer', 7: 'summer', 8: 'summer',
                9: 'autumn', 10: 'autumn', 11: 'autumn'
            }).iloc[0]  # Map month to season

            # Converteer seizoensinformatie naar one-hot encoding
            weather_df = pd.DataFrame([weather_data])
            weather_df = pd.get_dummies(weather_df, columns=['season'], drop_first=True)

            # Zorg dat alle seizoenskolommen aanwezig zijn
            for season in ['season_spring', 'season_summer', 'season_autumn']:
                if season not in weather_df.columns:
                    logging.warning(f"Kolom {season} ontbreekt; toegevoegd met standaardwaarde 0.")
                    weather_df[season] = 0

            return weather_df.iloc[0].to_dict()  # Zet terug naar dictionary
        except (KeyError, IndexError) as e:
            raise Exception("Fout bij het verwerken van de weerdata.") from e
    else:
        raise Exception(f"Fout bij het ophalen van weerdata: {response.status_code}")


def predict_weather(location):
    """
    Voorspelt VVN, VVX en de wolkenbasis op basis van real-time weerdata.
    """
    real_time_data = fetch_real_time_weather(location)
    input_data = pd.DataFrame([real_time_data])

    # Features per model
    vvn_expected_features = get_expected_features(vvn_model)
    vvx_expected_features = get_expected_features(vvx_model)
    cloud_base_expected_features = get_expected_features(cloud_base_model)

    # Synchroniseer invoerdata met de verwachte features
    vvn_input = synchronize_features(input_data, vvn_expected_features)
    vvx_input = synchronize_features(input_data, vvx_expected_features)
    cloud_base_input = synchronize_features(input_data, cloud_base_expected_features)

    # Voorspellingen maken
    vvn_prediction = vvn_model.predict(vvn_input)[0]
    vvx_prediction = vvx_model.predict(vvx_input)[0]
    cloud_base_prediction = cloud_base_model.predict(cloud_base_input)[0]

    return {
        "VVN": vvn_prediction,
        "VVX": vvx_prediction,
        "cloud_base": cloud_base_prediction
    }


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


# Main
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
