FROM python:3.11-slim  
WORKDIR /main          # Stel de werkdirectory in

# Kopieer de vereiste bestanden naar de container
COPY ./organized_server_script_v2.6.py /main/
COPY ./requirements.txt /main/
COPY ./models /main/models
COPY ./static /main/static
COPY ./templates /main/templates

# Installeer systeemafhankelijkheden en Python-pakketten
RUN apt-get update \
    && apt-get install -y \
    build-essential \
    libgomp1 \
    && apt-get clean \
    && pip install --no-cache-dir -r /main/requirements.txt

# Stel het startcommando in
CMD ["python", "/main/organized_server_script_v2.6.py"]
