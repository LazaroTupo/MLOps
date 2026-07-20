-- ============================================================
-- BASE DE DATOS MINI-SOAR
-- Generador de tráfico, modelo de detección y gestión de alertas
-- ============================================================


-- ============================================================
-- 1. TABLA DE TRÁFICO DE RED
-- ============================================================

CREATE TABLE IF NOT EXISTS network_traffic (
    id SERIAL PRIMARY KEY,

    -- Fecha y hora en la que fue generado el evento
    event_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Información de red
    source_ip VARCHAR(45) NOT NULL DEFAULT '192.168.1.100',
    destination_ip VARCHAR(45) NOT NULL DEFAULT '10.0.0.10',
    protocol VARCHAR(10) NOT NULL DEFAULT 'TCP',
    destination_port INTEGER NOT NULL DEFAULT 0,

    -- Características del tráfico
    duration DOUBLE PRECISION NOT NULL DEFAULT 0,
    packet_size INTEGER NOT NULL DEFAULT 0,
    connections INTEGER NOT NULL DEFAULT 1,

    -- Tipo de simulación
    scenario VARCHAR(50) NOT NULL DEFAULT 'dataset',

    -- Datos compatibles con el modelo de machine learning
    payload JSONB NOT NULL,

    -- Control del flujo n8n
    processed BOOLEAN NOT NULL DEFAULT FALSE,

    -- Fecha de procesamiento por n8n
    processed_at TIMESTAMP NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_destination_port
        CHECK (
            destination_port >= 0
            AND destination_port <= 65535
        ),

    CONSTRAINT valid_duration
        CHECK (duration >= 0),

    CONSTRAINT valid_packet_size
        CHECK (packet_size >= 0),

    CONSTRAINT valid_connections
        CHECK (connections >= 0)
);


-- Índice para que n8n encuentre rápidamente eventos pendientes
CREATE INDEX IF NOT EXISTS idx_network_traffic_processed
ON network_traffic(processed);


-- Índice para consultar por escenario
CREATE INDEX IF NOT EXISTS idx_network_traffic_scenario
ON network_traffic(scenario);


-- Índice para consultar por IP de origen
CREATE INDEX IF NOT EXISTS idx_network_traffic_source_ip
ON network_traffic(source_ip);


-- Índice para ordenar por fecha
CREATE INDEX IF NOT EXISTS idx_network_traffic_timestamp
ON network_traffic(event_timestamp);


-- ============================================================
-- 2. TABLA DE SIMULACIONES
-- ============================================================

CREATE TABLE IF NOT EXISTS traffic_simulations (
    id SERIAL PRIMARY KEY,

    scenario VARCHAR(50) NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING',

    requested_duration INTEGER NOT NULL,

    generated_events INTEGER NOT NULL DEFAULT 0,

    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    finished_at TIMESTAMP NULL,

    CONSTRAINT valid_simulation_status
        CHECK (
            status IN (
                'RUNNING',
                'COMPLETED',
                'STOPPED',
                'FAILED'
            )
        ),

    CONSTRAINT valid_requested_duration
        CHECK (requested_duration > 0),

    CONSTRAINT valid_generated_events
        CHECK (generated_events >= 0)
);


CREATE INDEX IF NOT EXISTS idx_traffic_simulations_status
ON traffic_simulations(status);


CREATE INDEX IF NOT EXISTS idx_traffic_simulations_scenario
ON traffic_simulations(scenario);


-- ============================================================
-- 3. TABLA DE INCIDENTES DEL MINI-SOAR
-- ============================================================

CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,

    ip_address VARCHAR(45) UNIQUE NOT NULL,

    status VARCHAR(50) NOT NULL DEFAULT 'OPEN',

    severity VARCHAR(50) NOT NULL DEFAULT 'LOW',

    occurrences INTEGER NOT NULL DEFAULT 1,

    average_probability DOUBLE PRECISION,

    first_detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    last_detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_incident_status
        CHECK (
            status IN (
                'OPEN',
                'CLOSED',
                'INVESTIGATING'
            )
        ),

    CONSTRAINT valid_incident_severity
        CHECK (
            severity IN (
                'LOW',
                'MEDIUM',
                'HIGH',
                'CRITICAL'
            )
        ),

    CONSTRAINT valid_occurrences
        CHECK (occurrences > 0),

    CONSTRAINT valid_probability
        CHECK (
            average_probability IS NULL
            OR (
                average_probability >= 0
                AND average_probability <= 1
            )
        )
);


CREATE INDEX IF NOT EXISTS idx_incidents_status
ON incidents(status);


CREATE INDEX IF NOT EXISTS idx_incidents_severity
ON incidents(severity);


-- ============================================================
-- 4. VISTA PARA CONSULTAR EVENTOS PENDIENTES
-- ============================================================

CREATE OR REPLACE VIEW pending_network_traffic AS
SELECT
    id,
    event_timestamp,
    source_ip,
    destination_ip,
    protocol,
    destination_port,
    duration,
    packet_size,
    connections,
    scenario,
    payload,
    processed,
    created_at
FROM network_traffic
WHERE processed = FALSE
ORDER BY id ASC;


-- ============================================================
-- 5. VISTA DE RESUMEN POR ESCENARIO
-- ============================================================

CREATE OR REPLACE VIEW traffic_scenario_summary AS
SELECT
    scenario,
    COUNT(*) AS total_events,
    COUNT(*) FILTER (WHERE processed = TRUE) AS processed_events,
    COUNT(*) FILTER (WHERE processed = FALSE) AS pending_events,
    MIN(event_timestamp) AS first_event,
    MAX(event_timestamp) AS last_event
FROM network_traffic
GROUP BY scenario;