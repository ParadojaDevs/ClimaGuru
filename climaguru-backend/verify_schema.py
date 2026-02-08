"""
Script de Verificacion de Consistencia Modelos vs Schema SQL
=============================================================
Este script compara los modelos SQLAlchemy con los esquemas SQL
para identificar inconsistencias antes de ejecutar migraciones.
"""

import re
from pathlib import Path

# ========== ANALISIS DE SQL ==========

SQL_FILE = "climaguru_database.sql"

def parse_sql_schema(sql_content):
    """Parsear el esquema SQL y extraer tablas y campos"""
    tables = {}
    
    # Dividir por CREATE TABLE
    lines = sql_content.split('\n')
    current_table = None
    current_fields = {}
    
    for line in lines:
        line = line.strip()
        
        # Buscar inicio de tabla
        create_match = re.match(r'CREATE TABLE\s+(\w+)\s*\(', line, re.IGNORECASE)
        if create_match:
            current_table = create_match.group(1)
            current_fields = {}
            continue
        
        # Si estamos dentro de una tabla
        if current_table:
            # Ignorar lineas de cierre e indices
            if line.startswith(')') or line.startswith('ENGINE') or line.startswith('UNIQUE') or line.startswith('INDEX') or line.startswith('FOREIGN') or line.startswith('--'):
                if line.startswith(')'):
                    tables[current_table] = current_fields
                    current_table = None
                continue
            
            # Parsear campo
            field_match = re.match(r'(\w+)\s+([A-Z]+(?:\([^\)]+\))?)', line, re.IGNORECASE)
            if field_match:
                field_name = field_match.group(1).lower()
                field_type = field_match.group(2).upper()
                
                # Ignorar PRIMARY KEY, FOREIGN KEY como campos
                if field_name not in ['primary', 'foreign', 'constraint', 'unique', 'index', 'key']:
                    current_fields[field_name] = field_type
    
    return tables

# ========== ANALISIS DE MODELOS PYTHON ==========

PYTHON_MODELS = {
    'usuarios': {
        'id': 'INTEGER',
        'username': 'VARCHAR(50)',
        'email': 'VARCHAR(100)',
        'password_hash': 'VARCHAR(255)',
        'nombre_completo': 'VARCHAR(100)',
        'rol': 'ENUM',
        'activo': 'BOOLEAN',
        'ultimo_login': 'DATETIME',
        'creado_en': 'TIMESTAMP',
        'actualizado_en': 'TIMESTAMP',
        'fecha_registro': 'DATETIME',
        'ultimo_acceso': 'DATETIME',
    },
    'api_keys': {
        'id': 'INTEGER',
        'usuario_id': 'INT',
        'proveedor': 'VARCHAR(50)',
        'api_key_encrypted': 'TEXT',
        'api_secret_encrypted': 'TEXT',
        'descripcion': 'VARCHAR(255)',
        'activa': 'BOOLEAN',
        'limite_consultas_diarias': 'INT',
        'consultas_realizadas': 'INT',
        'ultimo_uso': 'DATETIME',
        'creada_en': 'TIMESTAMP',
        'actualizada_en': 'TIMESTAMP',
        'servicio_nombre': 'VARCHAR(50)',
        'api_key': 'VARCHAR(255)',
        'fecha_registro': 'DATETIME',
        'fecha_actualizacion': 'DATETIME',
    },
    'consultas': {
        'id': 'INTEGER',
        'usuario_id': 'INT',
        'tipo_consulta': 'ENUM',
        'ciudad': 'VARCHAR(100)',
        'latitud': 'DECIMAL(10, 8)',
        'longitud': 'DECIMAL(11, 8)',
        'fecha_inicio': 'DATE',
        'fecha_fin': 'DATE',
        'formato_salida': 'ENUM',
        'parametros_solicitados': 'JSON',
        'respuesta_api': 'JSON',
        'estado': 'ENUM',
        'mensaje_error': 'TEXT',
        'tiempo_respuesta_ms': 'INT',
        'ip_origen': 'VARCHAR(45)',
        'creada_en': 'TIMESTAMP',
        'completada_en': 'DATETIME',
        'fecha_consulta': 'TIMESTAMP',
        'servicio_utilizado': 'VARCHAR(50)',
        'exitosa': 'BOOLEAN',
    },
    'datos_clima': {
        'id': 'INTEGER',
        'consulta_id': 'INT',
        'temperatura_promedio': 'DECIMAL(5, 2)',
        'temperatura_min': 'DECIMAL(5, 2)',
        'temperatura_max': 'DECIMAL(5, 2)',
        'presion_atmosferica': 'DECIMAL(8, 2)',
        'humedad_relativa': 'INT',
        'velocidad_viento': 'DECIMAL(5, 2)',
        'direccion_viento': 'INT',
        'precipitacion': 'DECIMAL(6, 2)',
        'visibilidad': 'INT',
        'indice_uv': 'DECIMAL(4, 2)',
        'calidad_aire': 'INT',
        'descripcion_clima': 'VARCHAR(100)',
        'fuentes_utilizadas': 'JSON',
        'datos_completos': 'JSON',
        'guardado_en': 'TIMESTAMP',
    },
    'sesiones': {
        'id': 'INTEGER',
        'usuario_id': 'INT',
        'token': 'VARCHAR(255)',
        'ip_address': 'VARCHAR(45)',
        'user_agent': 'TEXT',
        'fecha_creacion': 'TIMESTAMP',
        'fecha_expiracion': 'TIMESTAMP',
        'activa': 'BOOLEAN',
    },
}

# ========== VERIFICACION ==========

def verificar_inconsistencias():
    """Verificar y reportar inconsistencias"""
    
    print("=" * 60)
    print("VERIFICACION DE CONSISTENCIA MODELOS vs SCHEMA SQL")
    print("=" * 60)
    
    # Cargar SQL
    sql_path = Path(SQL_FILE)
    if sql_path.exists():
        with open(sql_path) as f:
            sql_content = f.read()
        sql_tables = parse_sql_schema(sql_content)
    else:
        print(f"[ERROR] No se encontro: {SQL_FILE}")
        return
    
    print(f"\n[INFO] Tablas encontradas en SQL: {len(sql_tables)}")
    print(f"[INFO] Modelos Python definidos: {len(PYTHON_MODELS)}")
    
    if sql_tables:
        print(f"[INFO] Tablas SQL: {list(sql_tables.keys())}")
    
    # Tablas en SQL pero no en Python
    sql_only = set(sql_tables.keys()) - set(PYTHON_MODELS.keys())
    if sql_only:
        print(f"\n[ERROR] TABLAS EN SQL SIN MODELO PYTHON:")
        for table in sql_only:
            print(f"   - {table}")
            print(f"     Campos: {list(sql_tables[table].keys())}")
    
    # Tablas en Python pero no en SQL
    python_only = set(PYTHON_MODELS.keys()) - set(sql_tables.keys())
    if python_only:
        print(f"\n[ERROR] MODELOS PYTHON SIN TABLA EN SQL:")
        for table in python_only:
            print(f"   - {table}")
            print(f"     Campos: {list(PYTHON_MODELS[table].keys())}")
    
    # Comparar campos comunes
    print("\n" + "=" * 60)
    print("COMPARACION DE CAMPOS POR TABLA")
    print("=" * 60)
    
    for table in sorted(set(sql_tables.keys()) & set(PYTHON_MODELS.keys())):
        print(f"\n[INFO] Tabla: {table}")
        
        sql_fields = sql_tables[table]
        py_fields = PYTHON_MODELS[table]
        
        # Campos en SQL pero no en Python
        sql_extra = set(sql_fields.keys()) - set(py_fields.keys())
        if sql_extra:
            print(f"   [WARN] En SQL, no en Python: {sorted(sql_extra)}")
        
        # Campos en Python pero no en SQL
        py_extra = set(py_fields.keys()) - set(sql_fields.keys())
        if py_extra:
            print(f"   [WARN] En Python, no en SQL: {sorted(py_extra)}")
        
        # Tipos diferentes
        type_mismatches = []
        for field in set(sql_fields.keys()) & set(py_fields.keys()):
            sql_type = sql_fields[field].upper().replace(' ', '')
            py_type = py_fields[field].upper().replace(' ', '')
            if sql_type != py_type:
                type_mismatches.append((field, sql_type, py_type))
        
        if type_mismatches:
            print(f"   [DIFF] Tipos diferentes:")
            for field, sql_type, py_type in type_mismatches:
                print(f"      - {field}: SQL={sql_type} vs Python={py_type}")
    
    print("\n" + "=" * 60)
    print("RESUMEN DE INCONSISTENCIAS")
    print("=" * 60)
    print(f"[ERROR] Tablas faltantes en Python: {len(sql_only)}")
    print(f"[ERROR] Modelos sin tabla: {len(python_only)}")
    print(f"[WARN] Diferencias de campos: REQUIERE REVISION MANUAL")
    print("\n[OK] Diagnostico completado.")

if __name__ == "__main__":
    verificar_inconsistencias()
