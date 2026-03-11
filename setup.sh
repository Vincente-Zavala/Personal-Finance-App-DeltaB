#!/bin/bash
echo "Launching DeltaB Finance Project..."

docker compose up -d --build

echo "Running Database Migrations to Supabase..."
docker compose exec web python manage.py migrate

echo "Success! Project is running at http://localhost:8000"