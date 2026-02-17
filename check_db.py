import pymysql
conn = pymysql.connect(host='100.78.215.44', user='climaguru_user', password='Pruebas2024', database='climaguru')
cursor = conn.cursor()
cursor.execute('DESCRIBE api_keys')
print('Columnas de api_keys:')
for col in cursor.fetchall():
    print(f'  {col[0]}: {col[1]}')
conn.close()
