-- =====================================================
-- CLIMAGURU - SCRIPT DE CORRECCIÓN DE BASE DE DATOS
-- =====================================================
-- Este script corrige las inconsistencias entre los modelos SQLAlchemy
-- y el esquema actual de la base de datos
-- 
-- Ejecutar: mysql -u root -p < fix_database.sql

USE climaguru;

-- =====================================================
-- 1. CORRECCIÓN: Tabla usuarios - Agregar columnas faltantes
-- =====================================================

-- Agregar columna fecha_registro si no existe
-- NOTA: Esta columna es un alias para creado_en, la agregamos para compatibilidad
ALTER TABLE usuarios 
ADD COLUMN IF NOT EXISTS fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER nombre_completo;

-- Agregar columna ultimo_acceso si no existe
ALTER TABLE usuarios 
ADD COLUMN IF NOT EXISTS ultimo_acceso TIMESTAMP NULL AFTER fecha_registro;

-- Verificar que las columnas existan
SELECT COLUMN_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'climaguru' 
AND TABLE_NAME = 'usuarios' 
AND COLUMN_NAME IN ('fecha_registro', 'ultimo_acceso');

-- =====================================================
-- 2. CREACIÓN: Tabla alertas_clima (falta en la base de datos)
-- =====================================================

CREATE TABLE IF NOT EXISTS alertas_clima (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    ciudad VARCHAR(100) NOT NULL,
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    tipo_alerta ENUM('temperatura_alta', 'temperatura_baja', 'lluvia', 'viento_fuerte', 'otro') NOT NULL,
    condicion JSON NOT NULL COMMENT 'Condición que activa la alerta',
    mensaje_personalizado VARCHAR(255),
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario (usuario_id),
    INDEX idx_ciudad (ciudad),
    INDEX idx_activa (activa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 3. CREACIÓN: Tabla configuraciones_usuario (falta en la base de datos)
-- =====================================================

CREATE TABLE IF NOT EXISTS configuraciones_usuario (
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

-- =====================================================
-- 4. Verificar tablas existentes
-- =====================================================

SELECT '=== TABLAS EN LA BASE DE DATOS ===' AS mensaje;
SHOW TABLES;

SELECT '=== VERIFICACIÓN DE TABLA USUARIOS ===' AS mensaje;
DESCRIBE usuarios;

SELECT '=== VERIFICACIÓN COMPLETADA ===' AS mensaje;
