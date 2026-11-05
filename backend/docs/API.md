# Documentación de API - ClimaGuru Backend

## Información General

- **URL Base**: `http://localhost:5000`
- **Puerto**: 5000
- **Base de datos**: SQLite (desarrollo local)

---

## Endpoints de Autenticación

### 1. Verificar estado del servidor

```bash
GET /health
```

**Respuesta exitosa:**
```json
{
  "status": "ok",
  "message": "ClimaGuru API está funcionando"
}
```

### 2. Registrar nuevo usuario

```bash
POST /api/auth/registro
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@ejemplo.com",
  "password": "Test1234",
  "nombre_completo": "Usuario de Prueba"
}
```

**Requisitos de contraseña:**
- Mínimo 8 caracteres
- Al menos una mayúscula
- Al menos una minúscula
- Al menos un número

### 3. Iniciar sesión

```bash
POST /api/auth/login
Content-Type: application/json

{
  "username_or_email": "testuser",
  "password": "Test1234"
}
```

**Respuesta exitosa:**
```json
{
  "mensaje": "Login exitoso",
  "usuario": {
    "id": 1,
    "username": "testuser",
    "email": "test@ejemplo.com",
    "nombre_completo": "Usuario de Prueba",
    "activo": true,
    "estadisticas": {
      "total_consultas": 0,
      "total_datos": 0,
      "api_keys_registradas": 0
    }
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 4. Obtener perfil del usuario actual

```bash
GET /api/auth/me
Authorization: Bearer {access_token}
```

### 5. Cerrar sesión

```bash
POST /api/auth/logout
Authorization: Bearer {access_token}
```

### 6. Refrescar token

```bash
POST /api/auth/refresh
Authorization: Bearer {refresh_token}
```

---

## Comandos cURL para Postman

### Verificar servidor
```bash
curl -X GET http://localhost:5000/health
```

### Registrar usuario
```bash
curl -X POST http://localhost:5000/api/auth/registro ^
  -H "Content-Type: application/json" ^
  -d "{\"username\": \"admin\", \"email\": \"admin@climaguru.com\", \"password\": \"Admin123\", \"nombre_completo\": \"Administrador\"}"
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username_or_email\": \"admin\", \"password\": \"Admin123\"}"
```

### Obtener perfil (con token)
```bash
curl -X GET http://localhost:5000/api/auth/me ^
  -H "Authorization: Bearer {access_token}"
```

---

## Configuración para Producción (MySQL)

Para conectar a la base de datos MySQL en la VM, modifica el archivo `.env`:

```env
# MySQL en VM
DB_HOST=100.78.215.44
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=climaguru
DATABASE_URL=mysql+pymysql://root:root@100.78.215.44:3306/climaguru
```

---

## Notas

- El servidor crea automáticamente las tablas en SQLite al iniciar
- Los tokens JWT expiran en 1 hora (configurable en .env)
- CORS está configurado para permitir todas las origenes (*)
