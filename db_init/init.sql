-- Inicialización de la base de datos para el proyecto Mini-SOAR (SoftInt)

-- 1. Tabla para simular el tráfico en tiempo real
-- ponytail: Usamos JSONB para guardar cualquier dataset (KDD, UNSW) sin tener que hardcodear 40+ columnas.
CREATE TABLE network_traffic (
    id SERIAL PRIMARY KEY,
    source_ip VARCHAR(50) DEFAULT '192.168.1.100', -- IP simulada para agrupar incidentes
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE
);

-- 2. Tabla de Incidentes (Mini-SOAR)
CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'OPEN',          -- OPEN, CLOSED, INVESTIGATING
    severity VARCHAR(50) DEFAULT 'LOW',         -- LOW, MEDIUM, HIGH, CRITICAL
    occurrences INTEGER DEFAULT 1,
    average_probability FLOAT,
    first_detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
