FROM python:3.11-slim

# Install dependencies for LightGBM and Python
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && apt-get clean

# Set the working directory
WORKDIR /app

# Copy project files to the container
COPY ./requirements.txt /app/
COPY ./organized_server_script_v2.6.py /app/
COPY ./models /app/models/
COPY ./static /app/static/
COPY ./templates /app/templates/
COPY ./templates/privacybeleid.html /app/templates/
COPY ./historical_weather_data.csv /app/
COPY ./requirements.txt /app/requirements.txt
# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Run the script
CMD ["python", "/app/organized_server_script_v2.6.py"]
