# Despliegue Rapido - ClimaGuru

Guia practica para desplegar backend (Flask) y frontend (Next.js) en Linux.

## 1) Requisitos

- Python 3.10+
- Node 20+
- Nginx
- MySQL 8 (local o remoto)
- Corepack habilitado (para usar pnpm)

## 2) Preparar entorno

```bash
cd /home/devhub/ClimaGuru
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend && pip install -r requirements.txt
cd ../frontend && corepack pnpm install
cd ..
```

## 3) Variables de entorno

### Backend

```bash
cd /home/devhub/ClimaGuru/backend
cp .env.example .env
```

Editar `.env` con valores reales:

```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=CAMBIAR_ESTA_CLAVE
JWT_SECRET_KEY=CAMBIAR_ESTA_CLAVE
DB_HOST=TU_HOST_MYSQL
DB_PORT=3306
DB_USER=TU_USUARIO_MYSQL
DB_PASSWORD=TU_PASSWORD_MYSQL
DB_NAME=climaguru
DATABASE_URL=mysql+pymysql://TU_USUARIO_MYSQL:TU_PASSWORD_MYSQL@TU_HOST_MYSQL:3306/climaguru
CORS_ORIGINS=https://tu-dominio-frontend.com
```

### Frontend

Crear archivo `/home/devhub/ClimaGuru/frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=https://tu-dominio-backend.com/api
```

Si frontend y backend comparten dominio por Nginx, tambien puede ser:

```env
NEXT_PUBLIC_API_URL=/api
```

## 4) Probar local antes de servicio

### Backend

```bash
cd /home/devhub/ClimaGuru
source .venv/bin/activate
cd backend
python app.py
```

Probar:

```bash
curl http://127.0.0.1:5000/health
```

### Frontend

```bash
cd /home/devhub/ClimaGuru/frontend
corepack pnpm build
corepack pnpm start
```

## 5) Servicio systemd para backend (Gunicorn)

Crear `/etc/systemd/system/climaguru-backend.service`:

```ini
[Unit]
Description=ClimaGuru Backend (Gunicorn)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/devhub/ClimaGuru/backend
Environment="PATH=/home/devhub/ClimaGuru/.venv/bin"
EnvironmentFile=/home/devhub/ClimaGuru/backend/.env
ExecStart=/home/devhub/ClimaGuru/.venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Activar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable climaguru-backend
sudo systemctl start climaguru-backend
sudo systemctl status climaguru-backend
```

## 6) Servicio systemd para frontend (Next.js)

Crear `/etc/systemd/system/climaguru-frontend.service`:

```ini
[Unit]
Description=ClimaGuru Frontend (Next.js)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/devhub/ClimaGuru/frontend
Environment="NODE_ENV=production"
ExecStart=/usr/bin/corepack pnpm start --host 127.0.0.1 --port 3000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Activar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable climaguru-frontend
sudo systemctl start climaguru-frontend
sudo systemctl status climaguru-frontend
```

## 7) Nginx reverse proxy

Crear `/etc/nginx/sites-available/climaguru`:

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://127.0.0.1:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activar sitio:

```bash
sudo ln -s /etc/nginx/sites-available/climaguru /etc/nginx/sites-enabled/climaguru
sudo nginx -t
sudo systemctl restart nginx
```

## 8) Verificaciones finales

```bash
curl -I http://127.0.0.1:3000
curl -I http://127.0.0.1:5000/health
curl -I http://tu-dominio.com
curl -I http://tu-dominio.com/health
```

## 9) Comandos de soporte

```bash
sudo journalctl -u climaguru-backend -f
sudo journalctl -u climaguru-frontend -f
sudo systemctl restart climaguru-backend
sudo systemctl restart climaguru-frontend
```

## 10) Seguridad minima antes de push

- No subir `.env`
- No subir claves reales en archivos `*.example`
- Rotar cualquier secreto que haya estado expuesto
- Revisar secretos antes de push:

```bash
git ls-files | rg -n "env|secret|key|token|password"
rg -n "AKIA|BEGIN PRIVATE KEY|SECRET_KEY=|JWT_SECRET_KEY=|DB_PASSWORD=|API_KEY=" .
```
