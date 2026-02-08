# Documentación de endpoints

Desde otra terminal o usando Postman:



# Verificar que el servidor está funcionando
curl http://localhost:5000/health

# Deberías recibir:
# {"status":"ok","message":"ClimaGuru API está funcionando"}

# Registrar un usuario
curl -X POST http://localhost:5000/api/auth/registro \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@ejemplo.com",
    "password": "Test1234",
    "nombre_completo": "Usuario de Prueba"
  }'





Documentar API
El backend está listo para recibir peticiones. Los endpoints disponibles son:
Autenticación (/api/auth/):

POST /registro - Registrar usuario
POST /login - Iniciar sesión
POST /refresh - Refrescar token
POST /logout - Cerrar sesión
GET /me - Información del usuario actual

Formato de respuesta:
json{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "usuario": {
    "id": 1,
    "username": "testuser",
    "email": "test@ejemplo.com"
  }
}


