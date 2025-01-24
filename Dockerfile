FROM python:3.11-slim

# Stel de werkdirectory in
WORKDIR /app

# Kopieer de requirements file naar de container
COPY requirements.txt /app/requirements.txt
COPY ./models /app/models
COPY ./static /app/static
COPY ./templates /app/templates

# Installeer afhankelijkheden
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de applicatie
COPY . /app

# Start het script
CMD ["python", "organized_server_script_v2.6.py"]
