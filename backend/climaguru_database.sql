-- =====================================================
-- CLIMAGURU - SCRIPT DE BASE DE DATOS MySQL
-- =====================================================
-- Ejecutar: mysql -u root -p < climaguru_database.sql

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS climaguru 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE climaguru;


-- =====================================================
-- TABLA: weather_observations
-- Observaciones meteorologicas normalizadas (IDEAM y SAB)
-- =====================================================
CREATE TABLE weather_observations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fuente ENUM('ideam_radar', 'sab_lluvias') NOT NULL,
    estacion VARCHAR(100),
    ciudad VARCHAR(100),
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    timestamp_observacion DATETIME NOT NULL,
    tipo_dato VARCHAR(50) NOT NULL,
    valor DECIMAL(12, 4),
    unidad VARCHAR(20),
    calidad VARCHAR(20) DEFAULT 'unknown',
    metadatos JSON,
    datos_crudos JSON,
    procesado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_fuente (fuente),
    INDEX idx_ciudad (ciudad),
    INDEX idx_coordenadas (latitud, longitud),
    INDEX idx_timestamp (timestamp_observacion),
    INDEX idx_tipo_dato (tipo_dato),
    INDEX idx_fuente_timestamp (fuente, timestamp_observacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
