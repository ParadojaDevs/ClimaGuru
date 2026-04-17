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
-- TABLA: usuarios
-- Almacena los operarios/usuarios del sistema
-- =====================================================
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(100),
    rol ENUM('admin', 'operario', 'consultor') DEFAULT 'operario',
    activo BOOLEAN DEFAULT TRUE,
    ultimo_login DATETIME,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_rol (rol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: api_keys
-- Almacena las API keys de cada proveedor por usuario
-- =====================================================
CREATE TABLE api_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    proveedor VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_secret_encrypted TEXT,
    descripcion VARCHAR(255),
    activa BOOLEAN DEFAULT TRUE,
    limite_consultas_diarias INT DEFAULT 1000,
    consultas_realizadas INT DEFAULT 0,
    ultimo_uso DATETIME,
    creada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_proveedor_usuario (usuario_id, proveedor),
    INDEX idx_proveedor (proveedor),
    INDEX idx_activa (activa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: consultas
-- Registra cada consulta realizada por los usuarios
-- =====================================================
CREATE TABLE consultas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tipo_consulta ENUM('tiempo_real', 'historico') NOT NULL,
    ciudad VARCHAR(100),
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    fecha_inicio DATE,
    fecha_fin DATE,
    formato_salida ENUM('json', 'csv', 'txt', 'yaml') DEFAULT 'json',
    parametros_solicitados JSON,
    respuesta_api JSON,
    estado ENUM('pendiente', 'procesando', 'completada', 'error') DEFAULT 'pendiente',
    mensaje_error TEXT,
    tiempo_respuesta_ms INT,
    ip_origen VARCHAR(45),
    creada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completada_en DATETIME,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario (usuario_id),
    INDEX idx_tipo (tipo_consulta),
    INDEX idx_estado (estado),
    INDEX idx_creada (creada_en),
    INDEX idx_ciudad (ciudad),
    INDEX idx_coordenadas (latitud, longitud)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: datos_clima
-- Almacena los datos procesados y promedios
-- =====================================================
CREATE TABLE datos_clima (
    id INT AUTO_INCREMENT PRIMARY KEY,
    consulta_id INT NOT NULL,
    temperatura_promedio DECIMAL(5, 2),
    temperatura_min DECIMAL(5, 2),
    temperatura_max DECIMAL(5, 2),
    presion_atmosferica DECIMAL(8, 2),
    humedad_relativa INT,
    velocidad_viento DECIMAL(5, 2),
    direccion_viento INT,
    precipitacion DECIMAL(6, 2),
    visibilidad INT,
    indice_uv DECIMAL(4, 2),
    calidad_aire INT,
    descripcion_clima VARCHAR(100),
    fuentes_utilizadas JSON,
    datos_completos JSON,
    guardado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (consulta_id) REFERENCES consultas(id) ON DELETE CASCADE,
    UNIQUE KEY unique_consulta (consulta_id),
    INDEX idx_temperatura (temperatura_promedio),
    INDEX idx_fecha (guardado_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: logs_actividad
-- Registro de actividad de usuarios (auditoría)
-- =====================================================
CREATE TABLE logs_actividad (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    accion VARCHAR(50) NOT NULL,
    detalle JSON,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    INDEX idx_usuario (usuario_id),
    INDEX idx_accion (accion),
    INDEX idx_fecha (creado_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: ciudades_favoritas
-- Ciudades guardadas por cada usuario
-- =====================================================
CREATE TABLE ciudades_favoritas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    nombre_ciudad VARCHAR(100) NOT NULL,
    pais VARCHAR(50),
    latitud DECIMAL(10, 8) NOT NULL,
    longitud DECIMAL(11, 8) NOT NULL,
    es_default BOOLEAN DEFAULT FALSE,
    creada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_ciudad_usuario (usuario_id, latitud, longitud),
    INDEX idx_usuario (usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: sesiones
-- Manejo de sesiones de usuario (JWT tokens)
-- =====================================================
CREATE TABLE sesiones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion DATETIME NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_usuario_activa (usuario_id, activa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- DATOS INICIALES
-- =====================================================

-- Usuario administrador por defecto
-- Contraseña: admin123 (cambiar en producción)
-- Generada con: bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
INSERT INTO usuarios (username, email, password_hash, nombre_completo, rol) VALUES 
('admin', 'admin@climaguru.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1K', 'Administrador', 'admin');

-- Usuario operario de ejemplo
-- Contraseña: operario123
INSERT INTO usuarios (username, email, password_hash, nombre_completo, rol) VALUES 
('operario1', 'operario1@climaguru.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1K', 'Operario Demo', 'operario');

-- =====================================================
-- VISTAS ÚTILES
-- =====================================================

-- Vista de consultas con datos del usuario
CREATE VIEW vista_consultas_completas AS
SELECT 
    c.id,
    c.tipo_consulta,
    c.ciudad,
    c.latitud,
    c.longitud,
    c.estado,
    c.creada_en,
    u.username,
    u.nombre_completo,
    dc.temperatura_promedio,
    dc.presion_atmosferica,
    dc.velocidad_viento
FROM consultas c
JOIN usuarios u ON c.usuario_id = u.id
LEFT JOIN datos_clima dc ON c.id = dc.consulta_id;

-- Vista de estadísticas por usuario
CREATE VIEW vista_estadisticas_usuarios AS
SELECT 
    u.id,
    u.username,
    u.nombre_completo,
    COUNT(c.id) as total_consultas,
    COUNT(CASE WHEN c.estado = 'completada' THEN 1 END) as consultas_exitosas,
    MAX(c.creada_en) as ultima_consulta
FROM usuarios u
LEFT JOIN consultas c ON u.id = c.usuario_id
WHERE u.activo = TRUE
GROUP BY u.id, u.username, u.nombre_completo;
