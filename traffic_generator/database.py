import time
from typing import Any

import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import Json

from config import (
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
)


def connect(
    max_attempts: int = 10,
    wait_seconds: int = 3
) -> connection:
    """
    Crea una conexión con PostgreSQL.

    Realiza varios intentos porque, al iniciar Docker Compose,
    PostgreSQL puede tardar algunos segundos en estar disponible.
    """

    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT
            )

        except psycopg2.OperationalError as error:
            last_error = error

            print(
                f"No se pudo conectar con PostgreSQL. "
                f"Intento {attempt}/{max_attempts}."
            )

            if attempt < max_attempts:
                time.sleep(wait_seconds)

    raise ConnectionError(
        "No se pudo establecer conexión con PostgreSQL."
    ) from last_error


def build_model_payload(event: dict[str, Any]) -> dict[str, Any]:
    """
    Convierte el evento sintético al formato aproximado utilizado
    por el dataset NSL-KDD.

    Los campos que no existen en el evento se completan con valores
    sintéticos coherentes. El modelo_service completa con cero los
    campos adicionales que no estén presentes.
    """

    scenario = event["scenario"]

    is_anomaly = scenario != "normal"

    protocol = event["protocol"].lower()

    destination_port = event["destination_port"]

    service_by_port = {
        20: "ftp_data",
        21: "ftp",
        22: "ssh",
        23: "telnet",
        25: "smtp",
        53: "domain_u",
        80: "http",
        110: "pop_3",
        143: "imap4",
        443: "http",
        993: "imap4",
        995: "pop_3",
        1433: "sql_net",
        3306: "private",
        3389: "private",
        5432: "private",
        8080: "http"
    }

    service = service_by_port.get(
        destination_port,
        "private"
    )

    connections = event["connections"]
    packet_size = event["packet_size"]

    if scenario in {"port_scan", "reconnaissance"}:
        flag = "REJ"
        serror_rate = 0.8
        same_srv_rate = 0.2
        diff_srv_rate = 0.8

    elif scenario in {"dos", "ddos"}:
        flag = "S0"
        serror_rate = 1.0
        same_srv_rate = 1.0
        diff_srv_rate = 0.0

    elif scenario == "brute_force":
        flag = "SF"
        serror_rate = 0.2
        same_srv_rate = 1.0
        diff_srv_rate = 0.0

    else:
        flag = "SF"
        serror_rate = 0.0
        same_srv_rate = 1.0
        diff_srv_rate = 0.0

    failed_logins = (
        min(connections, 50)
        if scenario == "brute_force"
        else 0
    )

    return {
        "duration": event["duration"],
        "protocol_type": protocol,
        "service": service,
        "flag": flag,
        "src_bytes": packet_size,
        "dst_bytes": max(packet_size // 2, 0),
        "land": 0,
        "wrong_fragment": 0,
        "urgent": 0,
        "hot": failed_logins,
        "num_failed_logins": failed_logins,
        "logged_in": 0 if is_anomaly else 1,
        "num_compromised": 0,
        "root_shell": 0,
        "su_attempted": 0,
        "num_root": 0,
        "num_file_creations": 0,
        "num_shells": 0,
        "num_access_files": 0,
        "num_outbound_cmds": 0,
        "is_host_login": 0,
        "is_guest_login": 0,
        "count": connections,
        "srv_count": connections,
        "serror_rate": serror_rate,
        "srv_serror_rate": serror_rate,
        "rerror_rate": 0.0,
        "srv_rerror_rate": 0.0,
        "same_srv_rate": same_srv_rate,
        "diff_srv_rate": diff_srv_rate,
        "srv_diff_host_rate": 0.0,
        "dst_host_count": min(connections, 255),
        "dst_host_srv_count": min(connections, 255),
        "dst_host_same_srv_rate": same_srv_rate,
        "dst_host_diff_srv_rate": diff_srv_rate,
        "dst_host_same_src_port_rate": 0.5,
        "dst_host_srv_diff_host_rate": 0.0,
        "dst_host_serror_rate": serror_rate,
        "dst_host_srv_serror_rate": serror_rate,
        "dst_host_rerror_rate": 0.0,
        "dst_host_srv_rerror_rate": 0.0,
        "class": "anomaly" if is_anomaly else "normal"
    }


def insert_event(event: dict[str, Any]) -> int:
    """
    Inserta un evento en network_traffic.

    Devuelve el ID creado.
    """

    payload = build_model_payload(event)

    query = """
        INSERT INTO network_traffic (
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
            processed
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            FALSE
        )
        RETURNING id;
    """

    conn = connect()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    event["timestamp"],
                    event["source_ip"],
                    event["destination_ip"],
                    event["protocol"],
                    event["destination_port"],
                    event["duration"],
                    event["packet_size"],
                    event["connections"],
                    event["scenario"],
                    Json(payload)
                )
            )

            inserted_id = cursor.fetchone()[0]

        conn.commit()

        return inserted_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def insert_events(events: list[dict[str, Any]]) -> int:
    """
    Inserta una lista completa de eventos dentro de una sola
    transacción.

    Devuelve la cantidad insertada.
    """

    if not events:
        return 0

    query = """
        INSERT INTO network_traffic (
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
            processed
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            FALSE
        );
    """

    records = []

    for event in events:
        payload = build_model_payload(event)

        records.append(
            (
                event["timestamp"],
                event["source_ip"],
                event["destination_ip"],
                event["protocol"],
                event["destination_port"],
                event["duration"],
                event["packet_size"],
                event["connections"],
                event["scenario"],
                Json(payload)
            )
        )

    conn = connect()

    try:
        with conn.cursor() as cursor:
            cursor.executemany(query, records)

        conn.commit()

        return len(records)

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def create_simulation(
    scenario: str,
    requested_duration: int
) -> int:
    """
    Registra el inicio de una simulación.
    """

    query = """
        INSERT INTO traffic_simulations (
            scenario,
            status,
            requested_duration,
            generated_events
        )
        VALUES (%s, 'RUNNING', %s, 0)
        RETURNING id;
    """

    conn = connect()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    scenario,
                    requested_duration
                )
            )

            simulation_id = cursor.fetchone()[0]

        conn.commit()

        return simulation_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def finish_simulation(
    simulation_id: int,
    status: str,
    generated_events: int
) -> None:
    """
    Actualiza el resultado final de una simulación.
    """

    query = """
        UPDATE traffic_simulations
        SET
            status = %s,
            generated_events = %s,
            finished_at = CURRENT_TIMESTAMP
        WHERE id = %s;
    """

    conn = connect()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    status,
                    generated_events,
                    simulation_id
                )
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def check_database_connection() -> bool:
    """
    Comprueba que PostgreSQL esté disponible.
    """

    try:
        conn = connect(
            max_attempts=1,
            wait_seconds=0
        )

        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()

        conn.close()

        return True

    except Exception:
        return False