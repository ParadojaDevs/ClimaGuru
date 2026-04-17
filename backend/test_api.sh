#!/bin/bash

# ===========================================
# Scripts de Prueba para ClimaGuru Backend
# ===========================================

BASE_URL="http://localhost:5000"
TOKEN=""

echo "=========================================="
echo "Pruebas de API ClimaGuru"
echo "=========================================="

# -------------------------------------------
# 1. Health Check
# -------------------------------------------
echo ""
echo ">>> 1. Health Check"
curl -s -X GET "$BASE_URL/health"
echo ""

# -------------------------------------------
# 2. Login (obtener token)
# -------------------------------------------
echo ""
echo ">>> 2. Login"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"testuser","password":"Test1234"}')

echo "$RESPONSE" | python -m json.tool 2>/dev/null || echo "$RESPONSE"

# Extraer token (usar python para Windows compatibility)
TOKEN=$(echo "$RESPONSE" | python -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "ERROR: No se pudo obtener el token"
  exit 1
fi

echo "Token obtenido: ${TOKEN:0:50}..."

# -------------------------------------------
# 3. Listar API Keys
# -------------------------------------------
echo ""
echo ">>> 3. Listar API Keys"
curl -s -X GET "$BASE_URL/api/api-keys/" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# -------------------------------------------
# 4. Crear API Key - OpenWeather
# -------------------------------------------
echo ""
echo ">>> 4. Crear API Key OpenWeather"
curl -s -X POST "$BASE_URL/api/api-keys/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"proveedor":"openweather","api_key":"90b742cedd679c807b83dc5de4b56d84","descripcion":"API de OpenWeather"}' | python -m json.tool

# -------------------------------------------
# 5. Crear API Key - Meteosource
# -------------------------------------------
echo ""
echo ">>> 5. Crear API Key Meteosource"
curl -s -X POST "$BASE_URL/api/api-keys/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"proveedor":"meteosource","api_key":"dnulnqrqaqe1sg2nkr33azllnhhkqpqqir573tmd","descripcion":"API de Meteosource"}' | python -m json.tool

# -------------------------------------------
# 6. Listar API Keys (verificar)
# -------------------------------------------
echo ""
echo ">>> 6. Listar API Keys (verificar)"
curl -s -X GET "$BASE_URL/api/api-keys/" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# -------------------------------------------
# 7. Consulta de Tiempo Real - Medellín
# -------------------------------------------
echo ""
echo ">>> 7. Consulta Tiempo Real - Medellín"
curl -s -X POST "$BASE_URL/api/consultas/tiempo-real" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"ciudad":"Medellin","proveedor":"openweather"}' | python -m json.tool

# -------------------------------------------
# 8. Consulta de Tiempo Real - Bogotá
# -------------------------------------------
echo ""
echo ">>> 8. Consulta Tiempo Real - Bogotá"
curl -s -X POST "$BASE_URL/api/consultas/tiempo-real" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"ciudad":"Bogota","proveedor":"meteosource"}' | python -m json.tool

# -------------------------------------------
# 9. Mis Consultas
# -------------------------------------------
echo ""
echo ">>> 9. Mis Consultas"
curl -s -X GET "$BASE_URL/api/consultas/mis-consultas" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# -------------------------------------------
# 10. Mi Perfil
# -------------------------------------------
echo ""
echo ">>> 10. Mi Perfil"
curl -s -X GET "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

echo ""
echo "=========================================="
echo "Pruebas completadas"
echo "=========================================="
