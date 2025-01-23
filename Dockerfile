# Basis image met Python
FROM python:3.11-slim

# Stel de werkdirectory in binnen de container
WORKDIR /app

# Kopieer je projectbestanden naar de container
COPY ./ /app

# Installeer vereisten vanuit requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Stel de standaard opdracht in om het script te draaien
CMD ["python", "organized_server_script_v2.6.py"]
