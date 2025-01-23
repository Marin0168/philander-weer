# Basis Python-image
FROM python:3.11-slim

# Installeer systeemafhankelijkheden voor LightGBM
RUN apt-get update && apt-get install -y \
    gcc \
    libgomp1 \
    && apt-get clean

# Stel de werkdirectory in
WORKDIR /app

# Kopieer de projectbestanden naar de container
COPY ../ /app

# Installeer Python-pakketten
RUN pip install --no-cache-dir -r requirements.txt

# Stel het startcommando in
CMD ["python", "organized_server_script_v2.6.py"]
