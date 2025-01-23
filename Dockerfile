# Gebruik een lichtgewicht Python-image
FROM python:3.11-slim

# Installeer systeemafhankelijkheden
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && apt-get clean

# Stel de werkdirectory in
WORKDIR /app

# Kopieer de vereiste bestanden naar de container
COPY ./requirements.txt /app/
COPY ./organized_server_script_v2.6.py /app/
COPY ./models /app/models/
COPY ./static /app/static/
COPY ./templates /app/templates/
COPY ./historical_weather_data.csv /app/

# Installeer Python-afhankelijkheden
RUN pip install --no-cache-dir -r requirements.txt

# Stel het startcommando in
CMD ["python", "/app/organized_server_script_v2.6.py"]
