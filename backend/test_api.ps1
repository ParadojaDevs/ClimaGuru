# ===========================================
# Scripts de Prueba para ClimaGuru Backend
# PowerShell Version
# ===========================================

$BASE_URL = "http://localhost:5000"
$TOKEN = ""

function Call-API {
    param(
        [string]$Method = "GET",
        [string]$Endpoint,
        [string]$Body = $null,
        [bool]$Auth = $false
    )
    
    $headers = @{"Content-Type" = "application/json"}
    if ($Auth -and $TOKEN) {
        $headers["Authorization"] = "Bearer $TOKEN"
    }
    
    $params = @{
        Method = $Method
        Uri = "$BASE_URL$Endpoint"
        Headers = $headers
    }
    
    if ($Body) {
        $params.Body = $Body
    }
    
    try {
        $response = Invoke-RestMethod @params
        return $response
    } catch {
        Write-Host "Error: $_" -ForegroundColor Red
        return $null
    }
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Pruebas de API ClimaGuru" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# -------------------------------------------
# 1. Health Check
# -------------------------------------------
Write-Host "`n>>> 1. Health Check" -ForegroundColor Yellow
$result = Call-API -Method GET -Endpoint "/health"
$result | ConvertTo-Json

# -------------------------------------------
# 2. Login (obtener token)
# -------------------------------------------
Write-Host "`n>>> 2. Login" -ForegroundColor Yellow
$body = @{
    username_or_email = "testuser"
    password = "Test1234"
} | ConvertTo-Json

$response = Call-API -Method POST -Endpoint "/api/auth/login" -Body $body
if ($response.access_token) {
    $TOKEN = $response.access_token
    Write-Host "Token obtenido: $($TOKEN.Substring(0, [Math]::Min(50, $TOKEN.Length)))..." -ForegroundColor Green
} else {
    Write-Host "ERROR: No se pudo obtener el token" -ForegroundColor Red
    exit 1
}

# -------------------------------------------
# 3. Listar API Keys
# -------------------------------------------
Write-Host "`n>>> 3. Listar API Keys" -ForegroundColor Yellow
$result = Call-API -Method GET -Endpoint "/api/api-keys/" -Auth $true
$result | ConvertTo-Json

# -------------------------------------------
# 4. Crear API Key - OpenWeather
# -------------------------------------------
Write-Host "`n>>> 4. Crear API Key OpenWeather" -ForegroundColor Yellow
$body = @{
    proveedor = "openweather"
    api_key = "90b742cedd679c807b83dc5de4b56d84"
    descripcion = "API de OpenWeather"
} | ConvertTo-Json

$result = Call-API -Method POST -Endpoint "/api/api-keys/" -Body $body -Auth $true
$result | ConvertTo-Json

# -------------------------------------------
# 5. Crear API Key - Meteosource
# -------------------------------------------
Write-Host "`n>>> 5. Crear API Key Meteosource" -ForegroundColor Yellow
$body = @{
    proveedor = "meteosource"
    api_key = "dnulnqrqaqe1sg2nkr33azllnhhkqpqqir573tmd"
    descripcion = "API de Meteosource"
} | ConvertTo-Json

$result = Call-API -Method POST -Endpoint "/api/api-keys/" -Body $body -Auth $true
$result | ConvertTo-Json

# -------------------------------------------
# 6. Listar API Keys (verificar)
# -------------------------------------------
Write-Host "`n>>> 6. Listar API Keys (verificar)" -ForegroundColor Yellow
$result = Call-API -Method GET -Endpoint "/api/api-keys/" -Auth $true
$result | ConvertTo-Json

# -------------------------------------------
# 7. Consulta de Tiempo Real - Medellín
# -------------------------------------------
Write-Host "`n>>> 7. Consulta Tiempo Real - Medellín" -ForegroundColor Yellow
$body = @{
    ciudad = "Medellin"
    proveedor = "openweather"
} | ConvertTo-Json

$result = Call-API -Method POST -Endpoint "/api/consultas/tiempo-real" -Body $body -Auth $true
$result | ConvertTo-Json

# -------------------------------------------
# 8. Consulta de Tiempo Real - Bogotá
# -------------------------------------------
Write-Host "`n>>> 8. Consulta Tiempo Real - Bogotá" -ForegroundColor Yellow
$body = @{
    ciudad = "Bogota"
    proveedor = "meteosource"
} | ConvertTo-Json

$result = Call-API -Method POST -Endpoint "/api/consultas/tiempo-real" -Body $body -Auth $true
$result | ConvertTo-Json

# -------------------------------------------
# 9. Mis Consultas
# -------------------------------------------
Write-Host "`n>>> 9. Mis Consultas" -ForegroundColor Yellow
$result = Call-API -Method GET -Endpoint "/api/consultas/mis-consultas" -Auth $true
$result | ConvertTo-Json

# -------------------------------------------
# 10. Mi Perfil
# -------------------------------------------
Write-Host "`n>>> 10. Mi Perfil" -ForegroundColor Yellow
$result = Call-API -Method GET -Endpoint "/api/auth/me" -Auth $true
$result | ConvertTo-Json

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "Pruebas completadas" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
