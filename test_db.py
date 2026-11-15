import pymysql

conn = pymysql.connect(
    host='100.78.215.44',
    port=3306,
    user='root',
    password='geCpezYdFIrpt',
    database='climaguru'
)
print('Conexión exitosa a MySQL')

# Verificar tablas
with conn.cursor() as cursor:
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    print('Tablas en la BD:', tables)
    # Verificar nuestras tablas nuevas
    for table in ['alertas_clima', 'configuraciones_usuario']:
        if table in tables:
            print(f'✅ Tabla {table} EXISTS')
        else:
            print(f'❌ Tabla {table} NOT FOUND')

conn.close()