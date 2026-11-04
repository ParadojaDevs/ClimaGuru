-- =====================================================
-- CLIMAGURU - SCRIPT DE CORRECCIÓN DE BASE DE DATOS
-- =====================================================
-- Este script corrige las inconsistencias entre los modelos SQLAlchemy
-- y el esquema actual de la base de datos
-- 
-- Ejecutar: mysql -u root -p climaguru < fix_database.sql

USE climaguru;

-- =====================================================
-- 1. CORRECCIÓN: Tabla usuarios - Agregar columnas faltantes
-- =====================================================

-- Verificar y agregar columna fecha_registro
SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'climaguru' AND TABLE_NAME = 'usuarios' AND COLUMN_NAME = 'fecha_registro';

IF @col_exists = 0 THEN
    ALTER TABLE usuarios ADD COLUMN fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER nombre_completo;
END IF;

-- Verificar y agregar columna ultimo_acceso
SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'climaguru' AND TABLE_NAME = 'usuarios' AND COLUMN_NAME = 'ultimo_acceso';

IF @col_exists = 0 THEN
    ALTER TABLE usuarios ADD COLUMN ultimo_acceso TIMESTAMP NULL AFTER fecha_registro;
END IF;

-- =====================================================
-- 2. CREACIÓN: Tabla alertas_clima (falta en la base de datos)
-- =====================================================

SELECT COUNT(*) INTO @table_exists FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'climaguru' AND TABLE_NAME = 'alertas_clima';

IF @table_exists = 0 THEN
    CREATE TABLE alertas_clima (
        id INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id INT NOT NULL,
        ciudad VARCHAR(100) NOT NULL,
        latitud DECIMAL(10, 8),
        longitud DECIMAL(11, 8),
        tipo_alerta ENUM('temperatura_alta', 'temperatura_baja', 'lluvia', 'viento_fuerte', 'otro') NOT NULL,
        condicion JSON NOT NULL,
        mensaje_personalizado VARCHAR(255),
        activa BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        actualizada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
        INDEX idx_usuario (usuario_id),
        INDEX idx_ciudad (ciudad),
        INDEX idx_activa (activa)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
END IF;

-- =====================================================
-- 3. CREACIÓN: Tabla configuraciones_usuario (falta en la base de datos)
-- =====================================================

SELECT COUNT(*) INTO @table_exists FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'climaguru' AND TABLE_NAME = 'configuraciones_usuario';

IF @table_exists = 0 THEN
    CREATE TABLE configuraciones_usuario (
        id INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id INT NOT NULL UNIQUE,
        tema_interfaz ENUM('claro', 'oscuro', 'auto') DEFAULT 'auto',
        unidades_temperatura ENUM('celsius', 'fahrenheit') DEFAULT 'celsius',
        idioma ENUM('es', 'en') DEFAULT 'es',
        notificaciones_email BOOLEAN DEFAULT TRUE,
        notificaciones_push BOOLEAN DEFAULT TRUE,
        ciudad_default VARCHAR(100),
        latitud_default DECIMAL(10, 8),
        longitud_default DECIMAL(11, 8),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        actualizada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
        INDEX idx_usuario (usuario_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
END IF;

-- =====================================================
-- 4. Verificar tablas existentes
-- =====================================================
SELECT '=== VERIFICACIÓN COMPLETADA ===' AS mensaje;
