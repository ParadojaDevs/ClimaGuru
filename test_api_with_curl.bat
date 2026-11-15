@echo off
title ClimaGuru API Tests with curl
echo.
echo ============================================
echo  ClimaGuru API Tests - curl based
echo ============================================
echo.

:: Configuración
set BASE_URL=http://localhost:5000
set USERNAME=admin
set PASSWORD=admin123

echo 1/4  Health Check
echo ----------------------------------------------------------
curl -i -X GET %BASE_URL%/health
echo.
echo.

echo 2/4  Login - Obtener tokens httpOnly cookies
echo ----------------------------------------------------------
echo "Realizando login con credenciales: %USERNAME% / %PASSWORD%"
curl -i -X POST -H "Content-Type: application/json" -d "{\"username\":\"%USERNAME%\",\"password\":\"%PASSWORD%\"}" %BASE_URL%/login
echo.
echo.

echo 3/4  Acceder a /users - Verificar que cookies se envían automáticamente
echo ----------------------------------------------------------
echo "Probando endpoint /users (requiere autenticación)"
echo "Las cookies httpOnly deberían enviarse automáticamente"
curl -i -b "climaguru_access_token=test; climaguru_refresh_token=test" -X GET %BASE_URL%/users
echo.
echo.

echo 4/4  Logout - Borrar cookies
echo ----------------------------------------------------------
echo "Realizando logout"
curl -i -X GET %BASE_URL%/logout
echo.
echo.

echo ============================================
echo  Pruebas completadas
echo ============================================
pause