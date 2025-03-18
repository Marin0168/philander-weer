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
COPY ./app.py /app/
COPY ./models /app/models/
COPY ./static /app/static/
COPY ./templates /app/templates/
COPY ./historical_weather_data.csv /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Run the script
CMD ["python", "/app/app.py"]
