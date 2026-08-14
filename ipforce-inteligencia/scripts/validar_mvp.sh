#!/usr/bin/env bash
set -euo pipefail
test -f .env || { echo "ERRO: crie .env a partir de .env.example"; exit 1; }
python3 -m compileall -q backend/app
grep -q "^PABX_BASE_URL=." .env || { echo "ERRO: PABX_BASE_URL ausente"; exit 1; }
grep -q "^PABX_API_KEY=." .env || { echo "ERRO: PABX_API_KEY ausente"; exit 1; }
grep -q "^SECRET_KEY=." .env || { echo "ERRO: SECRET_KEY ausente"; exit 1; }
docker compose config >/dev/null
echo "Ambiente base OK. Proximo passo: docker compose up --build -d"
