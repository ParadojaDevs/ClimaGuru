# Guía de instalación

Configura y ejecuta

Edita el archivo .env con tus datos
Activa el entorno virtual: source venv/bin/activate
Instala dependencias: pip install -r requirements.txt
Inicializa BD: flask db init && flask db migrate && flask db upgrade
Ejecuta: python3 run.py

Prueba

Verifica: curl http://localhost:5000/health
Registra usuario (ejemplo en README.md)
Prueba login


# Activar entorno virtual
source ~/ClimaGuru/backend/venv/bin/activate

# Ver logs en tiempo real
sudo journalctl -u climaguru -f

# Reiniciar backend
sudo systemctl restart climaguru

# Probar endpoint
curl http://localhost:5000/health