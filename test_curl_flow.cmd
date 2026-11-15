@echo off
title ClimaGuru API Testing with curl
setlocal enabledelayedexpansion

:: Configuración
set BASE_URL=http://localhost:5000
set CREDS="{\"username\":\"admin\",\"password\":\"admin123\"}"

echo.
echo ============================================
echo  ClimaGuru API Flow Test - curl
echo ============================================
echo.

:: 1. Health Check
echo 1/4  Health Check
echo ----------------------------------------------------------
curl -s -X GET %BASE_URL%/health
echo.
echo.

:: 2. Login - Obtener respuesta con Set-Cookie headers
echo 2/4  Login - Obtener tokens (guardaremos cookies en archivo)
echo ----------------------------------------------------------
echo "Realizando login..."
curl -c cookies.txt -X POST -H "Content-Type: application/json" -d %CREDS% %BASE_URL%/login
echo.
echo "Headers de respuesta (buscando Set-Cookie):"
curl -D - -X POST -H "Content-Type: application/json" -d %CREDS% %BASE_URL%/login 2>findstr "Set-Cookie" || echo "   (No se encontraron cookies o servidor no corriendo)"
echo.
echo "Cookies guardadas en cookies.txt:"
type cookies.txt
echo.
echo.

:: 3. Acceder a /users - Usar cookies guardadas
echo 3/4  Acceder a /users - Probar con cookies guardadas
echo ----------------------------------------------------------
echo "Probando endpoint /users con cookies autenticadas:"
curl -b cookies.txt -X GET %BASE_URL%/users
echo.
echo.
echo.

:: 4. Verificar estado de login
echo 4/4  Verificar sesión activa
echo ----------------------------------------------------------
echo "Verificando que la sesión está activa..."
curl -s -o /dev/null -w "   Status code: %HTTP_CODE%" -b cookies.txt -X GET %BASE_URL%/users
echo.
echo.

:: Limpiar
echo Limpiando cookies...
del cookies.txt

echo.
echo ============================================
echo  Flujo de prueba completado
echo ============================================
echo.
echo Instrucciones para ejecución:
echo 1. Levantar el servidor: python app.py (en backend/)
echo 2. Ejecutar este script: test_curl_flow.cmd
echo 3. Revisar los outputs de cada paso
echo.
pause