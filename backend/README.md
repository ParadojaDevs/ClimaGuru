# Backend Flask - ClimaGuru

API REST limpia para autenticacion y CRUD de usuarios.

## Estructura

- app.py
- config.py
- routes/
- models/
- database/

## Endpoints

- POST /login
- GET /users
- POST /users
- PUT /users/<id>
- DELETE /users/<id>
- GET /health

## Ejecutar

```bash
cd backend
pip install -r requirements.txt
python app.py
```

## Configuracion de base de datos (MySQL)

La aplicacion usa MySQL por defecto.

Opciones de configuracion:

1. `DATABASE_URL` completa (recomendado).
2. Variables separadas `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`.

Ejemplos disponibles:

- `.env.example`
- `.env.production.example`
- `.env.local.example`

## Conexion por Tailscale a VM MySQL

### Produccion (en la VM)

1. Instala y conecta Tailscale en la VM.
2. Verifica que MySQL escuche en la interfaz esperada (`127.0.0.1` o IP Tailscale).
3. Configura reglas de firewall para permitir solo la red Tailscale.
4. Usa `.env.production.example` como base.

### Pruebas locales (desde tu equipo)

1. Inicia sesion en Tailscale local y confirma conectividad con la VM.
2. Usa la IP Tailscale de la VM como `MYSQL_HOST` (ejemplo `100.x.y.z`).
3. Carga `.env.local.example` y ajusta credenciales.

Prueba conectividad rapida:

```bash
# Desde tu equipo local
ping 100.x.y.z
```

Validar conexion desde Python:

```bash
cd backend
python database/check_mysql_connection.py
```

Guia detallada:

- `database/TAILSCALE_MYSQL.md`

## Postman (coleccion automatica)

Archivos incluidos:

- `postman_collection.json`
- `postman_environment.json`

Flujo automatizado en orden:

1. `Health`
2. `Auth - Login`
3. `Users - Create`
4. `Users - List`
5. `Users - Update`
6. `Users - Delete`
7. `Users - Verify Deleted`

Las pruebas guardan y reutilizan:

- `auth_token`
- `test_user_id`

Incluye validaciones de status codes, campos JSON y tiempos de respuesta.

## Credenciales iniciales

Se crea automaticamente:

- username: admin
- password: admin123

## Notas de autenticacion

- Realiza POST /login para obtener token.
- En las rutas /users usa header:
  - Authorization: Bearer <token>
