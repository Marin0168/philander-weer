#!/bin/bash
docker compose down
git pull
docker build -t philander-weerapp:V1 ~/docker/philander-weer
docker-compose up -d --remove-orphans


