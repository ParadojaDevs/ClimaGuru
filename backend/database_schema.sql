-- ===================================
-- CLIMAGURU - DATABASE SCHEMA
-- ===================================

CREATE DATABASE IF NOT EXISTS climaguru_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE climaguru_db;

-- Tabla de Usuarios/Operarios
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(100),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP NULL,
    activo BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB;

-- Tabla de API Keys por usuario
CREATE TABLE api_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    servicio_nombre VARCHAR(50) NOT NULL COMMENT 'Ej: OpenWeatherMap, WeatherAPI, etc.',
    api_key VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    activa BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_service (usuario_id, servicio_nombre),
    INDEX idx_usuario (usuario_id)
) ENGINE=InnoDB;

-- Tabla de Consultas Realizadas
CREATE TABLE consultas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tipo_consulta ENUM('tiempo_real', 'historico') NOT NULL,
    ciudad VARCHAR(100),
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    fecha_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    servicio_utilizado VARCHAR(50) COMMENT 'API que se utilizó para la consulta',
    tiempo_respuesta_ms INT COMMENT 'Tiempo de respuesta en milisegundos',
    exitosa BOOLEAN DEFAULT TRUE,
    mensaje_error TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario_fecha (usuario_id, fecha_consulta),
    INDEX idx_ciudad (ciudad),
    INDEX idx_coordenadas (latitud, longitud)
) ENGINE=InnoDB;

-- Tabla de Datos Meteorológicos
CREATE TABLE datos_meteorologicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    consulta_id INT NOT NULL,
    usuario_id INT NOT NULL,
    
    -- Información de ubicación
    ciudad VARCHAR(100),
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    
    -- Timestamp de los datos
    fecha_hora_dato TIMESTAMP NOT NULL COMMENT 'Fecha/hora del dato meteorológico',
    fecha_hora_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Cuándo se guardó en la BD',
    
    -- Datos meteorológicos principales
    temperatura DECIMAL(5, 2) COMMENT 'Temperatura en Celsius',
    sensacion_termica DECIMAL(5, 2),
    temperatura_min DECIMAL(5, 2),
    temperatura_max DECIMAL(5, 2),
    
    presion_atmosferica DECIMAL(6, 2) COMMENT 'Presión en hPa',
    humedad INT COMMENT 'Humedad relativa en %',
    
    velocidad_viento DECIMAL(5, 2) COMMENT 'Velocidad del viento en m/s',
    direccion_viento INT COMMENT 'Dirección del viento en grados',
    rafaga_viento DECIMAL(5, 2) COMMENT 'Ráfagas en m/s',
    
    precipitacion DECIMAL(6, 2) COMMENT 'Precipitación en mm',
    nubosidad INT COMMENT 'Cobertura de nubes en %',
    visibilidad INT COMMENT 'Visibilidad en metros',
    
    descripcion VARCHAR(255) COMMENT 'Descripción del clima',
    icono VARCHAR(50) COMMENT 'Código del icono del clima',
    
    -- Metadata
    fuente_dato VARCHAR(50) COMMENT 'API de origen del dato',
    datos_raw JSON COMMENT 'Datos crudos en formato JSON para referencia',
    
    FOREIGN KEY (consulta_id) REFERENCES consultas(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario_fecha (usuario_id, fecha_hora_dato),
    INDEX idx_ciudad_fecha (ciudad, fecha_hora_dato),
    INDEX idx_coordenadas (latitud, longitud)
) ENGINE=InnoDB;

-- Tabla de Promedios Calculados (para optimizar consultas frecuentes)
CREATE TABLE promedios_climaticos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    ciudad VARCHAR(100),
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    
    -- Período del promedio
    tipo_periodo ENUM('hora', 'dia', 'semana', 'mes') NOT NULL,
    fecha_inicio TIMESTAMP NOT NULL,
    fecha_fin TIMESTAMP NOT NULL,
    
    -- Promedios
    temperatura_promedio DECIMAL(5, 2),
    temperatura_min DECIMAL(5, 2),
    temperatura_max DECIMAL(5, 2),
    presion_promedio DECIMAL(6, 2),
    humedad_promedio DECIMAL(5, 2),
    velocidad_viento_promedio DECIMAL(5, 2),
    precipitacion_total DECIMAL(6, 2),
    
    cantidad_datos INT COMMENT 'Número de datos usados para el promedio',
    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario_periodo (usuario_id, tipo_periodo, fecha_inicio),
    INDEX idx_ciudad_periodo (ciudad, tipo_periodo, fecha_inicio)
) ENGINE=InnoDB;

-- Tabla de Sesiones (para manejo de autenticación)
CREATE TABLE sesiones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion TIMESTAMP NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_usuario_activa (usuario_id, activa)
) ENGINE=InnoDB;

-- Vista para consultas frecuentes de usuarios
CREATE VIEW vista_actividad_usuarios AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.fecha_registro,
    u.ultimo_acceso,
    COUNT(DISTINCT c.id) as total_consultas,
    COUNT(DISTINCT dm.id) as total_datos_guardados,
    MAX(c.fecha_consulta) as ultima_consulta
FROM usuarios u
LEFT JOIN consultas c ON u.id = c.usuario_id
LEFT JOIN datos_meteorologicos dm ON u.id = dm.usuario_id
GROUP BY u.id, u.username, u.email, u.fecha_registro, u.ultimo_acceso;

-- Procedimiento almacenado para calcular promedios
DELIMITER //

CREATE PROCEDURE calcular_promedio_periodo(
    IN p_usuario_id INT,
    IN p_ciudad VARCHAR(100),
    IN p_tipo_periodo ENUM('hora', 'dia', 'semana', 'mes'),
    IN p_fecha_inicio TIMESTAMP,
    IN p_fecha_fin TIMESTAMP
)
BEGIN
    INSERT INTO promedios_climaticos (
        usuario_id, ciudad, latitud, longitud,
        tipo_periodo, fecha_inicio, fecha_fin,
        temperatura_promedio, temperatura_min, temperatura_max,
        presion_promedio, humedad_promedio, velocidad_viento_promedio,
        precipitacion_total, cantidad_datos
    )
    SELECT 
        p_usuario_id,
        p_ciudad,
        AVG(latitud),
        AVG(longitud),
        p_tipo_periodo,
        p_fecha_inicio,
        p_fecha_fin,
        AVG(temperatura),
        MIN(temperatura_min),
        MAX(temperatura_max),
        AVG(presion_atmosferica),
        AVG(humedad),
        AVG(velocidad_viento),
        SUM(precipitacion),
        COUNT(*)
    FROM datos_meteorologicos
    WHERE usuario_id = p_usuario_id
        AND ciudad = p_ciudad
        AND fecha_hora_dato BETWEEN p_fecha_inicio AND p_fecha_fin
    HAVING COUNT(*) > 0;
END //

DELIMITER ;
