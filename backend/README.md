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

## Credenciales iniciales

Se crea automaticamente:

- username: admin
- password: admin123

## Notas de autenticacion

- Realiza POST /login para obtener token.
- En las rutas /users usa header:
  - Authorization: Bearer <token>
