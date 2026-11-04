-- =====================================================
-- CLIMAGURU - SCRIPT DE CORRECCIÓN SIMPLE
-- =====================================================
-- Ejecutar estos comandos directamente en MySQL

-- 1. Agregar columnas faltantes a tabla usuarios
ALTER TABLE usuarios ADD COLUMN fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER nombre_completo;
ALTER TABLE usuarios ADD COLUMN ultimo_acceso TIMESTAMP NULL AFTER fecha_registro;

-- 2. Crear tabla alertas_clima
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

-- 3. Crear tabla configuraciones_usuario
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
