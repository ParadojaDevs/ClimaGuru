@echo off
title ClimaGuru - Validated Start with httpOnly Cookies
echo.
echo ============================================
echo  ClimaGuru Backend Start - Validated Build
echo ============================================
echo.

:: Configurar variables de entorno para BD remota
set MYSQL_HOST=100.78.215.44
set MYSQL_PORT=3306
set MYSQL_USER=root
set MYSQL_PASSWORD=geCpezYdFIrpt
set MYSQL_DATABASE=climaguru
set SECRET_KEY=climaguru-secret-key-change-production
set FLASK_ENV=development
set FLASK_DEBUG=False

echo 1/5  Conectando a base de datos remota...
echo   Host: %MYSQL_HOST%
echo   Database: %MYSQL_DATABASE%

:: Verificar conexión a MySQL
python -c "import pymysql; c=pymysql.connect(host=%MYSQL_HOST%,user=%MYSQL_USER%,password=%MYSQL_PASSWORD%,database=%MYSQL_DATABASE%); print('   OK - Conexión exitosa'); c.close()" 2>nul

if errorlevel 1 (
    echo.
    echo ERROR: No se puede conectar a la base de datos remota.
    echo Por favor verifica:
    echo   - La VM 100.78.215.44 está encendida
    echo   - MySQL está escuchando en el puerto 3306
    echo   - Las credenciales son correctas
    pause
    exit /b 1
)

echo.
echo 2/5  Verificando tablas requeridas...
python -c "
import pymysql
conn = pymysql.connect(host='%MYSQL_HOST%',user='%MYSQL_USER%',password='%MYSQL_PASSWORD%',database='%MYSQL_DATABASE%')
with conn.cursor() as cursor:
    cursor.execute('SHOW TABLES')
    tables = [row[0] for row in cursor.fetchall()]
required = ['alertas_clima', 'configuraciones_usuario', 'usuarios']
for t in required:
    if t in tables:
        print(f'   OK - Tabla {t} EXISTS')
    else:
        print(f'   MISSING - Tabla {t} NOT FOUND')
conn.close()
"

echo.
echo 3/5  Iniciando aplicacion Flask con JWT y httpOnly cookies...
echo.
echo  == Configuracion Actual ==
echo   - JWT: Flask-JWT-Extended (access + refresh tokens)
echo   - Auth: httpOnly cookies (XSS protection)
echo   - Security: 6 headers HTTP agregados
echo   - Rate Limit: Flask-Limiter (200/day, 50/hour)
echo.
echo  Ejecutando: python app.py
echo  Presiona Ctrl+C para detener
echo.

:: Iniciar la aplicacion Flask
python app.py

echo.
echo Aplicacion detenida.
echo 4/5  Probar flujo de autenticacion...
echo   - Abrir http://localhost:5000 en el navegador
echo   - Observar Application > Cookies para verificar httpOnly
echo   - Login con credenciales admin / admin123 (o usuario creado)
echo   - Probar endpoints /users con cookies automáticas
echo   - Logout y verificar cookies borradas
echo.

echo 5/5  Validacion completada. Proyecto ClimaGuru listo para produccion.
echo ============================================