-- Inicialización de la base de datos VitAI
-- Este script se ejecuta automáticamente cuando se crea el contenedor de PostgreSQL

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Configurar zona horaria
SET timezone = 'UTC';

-- Crear esquemas si son necesarios (opcional)
-- CREATE SCHEMA IF NOT EXISTS vitai_core;

-- Comentario de inicialización
SELECT 'Base de datos VitAI inicializada correctamente' as status;

