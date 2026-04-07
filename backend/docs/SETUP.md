# Guia de instalacion

## Configura y ejecuta

1. Entra al backend:

```bash
cd ~/ClimaGuru/backend
```

2. Crea y activa el entorno virtual (compartido en la raiz):

```bash
python3 -m venv ../.venv
source ../.venv/bin/activate
```

3. Instala dependencias:

```bash
pip install -r requirements.txt
```

4. Configura variables de entorno:

```bash
cp .env.example .env
```

5. Edita `.env` con tu conexion de base de datos y secretos JWT.

6. Ejecuta backend:

```bash
python3 app.py
```

## Pruebas rapidas

```bash
curl http://localhost:5000/health
```

## Operacion en servidor

Ver logs en tiempo real:

```bash
sudo journalctl -u climaguru -f
```

Reiniciar backend:

```bash
sudo systemctl restart climaguru
```