# Conexion MySQL via Tailscale (Local y Produccion)

## Objetivo

Conectar el backend Flask a MySQL de una VM a traves de la red privada Tailscale.

## 1) Requisitos minimos

- Tailscale instalado en la VM y en el equipo local.
- Ambos nodos autenticados en el mismo tailnet.
- Servicio MySQL activo en la VM.

## 2) Verificacion de red

En el equipo local:

```bash
# Reemplaza por la IP Tailscale real de la VM
ping 100.x.y.z
```

Si responde, valida el puerto:

```bash
# PowerShell
Test-NetConnection 100.x.y.z -Port 3306
```

## 3) Configuracion MySQL en la VM

- Crea un usuario dedicado para la app (principio de minimo privilegio).
- Permite acceso solo desde red Tailscale.
- Evita exponer 3306 a internet publico.

Ejemplo SQL base:

```sql
CREATE USER 'climaguru_app'@'100.%' IDENTIFIED BY 'cambia-esta-clave';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX ON climaguru.* TO 'climaguru_app'@'100.%';
FLUSH PRIVILEGES;
```

Ajusta host del usuario segun tu politica (`100.%`, host especifico, o ACL de Tailscale).

## 4) Configuracion del backend

Usa `.env.local.example` para pruebas locales y `.env.production.example` para VM.

Variables clave:

- `MYSQL_HOST=100.x.y.z`
- `MYSQL_PORT=3306`
- `MYSQL_USER=climaguru_app`
- `MYSQL_PASSWORD=...`
- `MYSQL_DATABASE=climaguru`

## 5) Prueba de conexion desde backend

```bash
cd backend
python database/check_mysql_connection.py
```

Resultado esperado:

- `[OK] Puerto MySQL accesible`
- `[OK] Conexion MySQL establecida. Version: ...`

## 6) Buenas practicas de seguridad

- No guardar secretos reales en Git.
- Rotar contrasenas periodicamente.
- Restringir permisos SQL por entorno (produccion vs pruebas).
- Usar ACL de Tailscale para limitar origenes y puertos.
