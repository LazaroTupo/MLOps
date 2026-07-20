import random
from datetime import datetime
from typing import Callable

from generator import random_ip


COMMON_PORTS = [
    20,
    21,
    22,
    23,
    25,
    53,
    80,
    110,
    135,
    139,
    143,
    443,
    445,
    993,
    995,
    1433,
    3306,
    3389,
    5432,
    8080
]


def create_event(
    source_ip: str,
    destination_ip: str,
    protocol: str,
    destination_port: int,
    duration: float,
    packet_size: int,
    connections: int,
    scenario: str
) -> dict:
    """
    Construye un registro de tráfico sintético.

    No realiza tráfico real en la red.
    Solo devuelve un diccionario que después será guardado
    en PostgreSQL.
    """

    return {
        "timestamp": datetime.now(),
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "protocol": protocol,
        "destination_port": destination_port,
        "duration": round(duration, 4),
        "packet_size": packet_size,
        "connections": connections,
        "scenario": scenario
    }


def normal_traffic(event_count: int = 10) -> list[dict]:
    """
    Simula tráfico normal de una red empresarial.

    Características:
    - IP de origen y destino variables.
    - Puertos comunes.
    - Duraciones moderadas.
    - Tamaños de paquete normales.
    - Pocas conexiones por evento.
    """

    events = []

    normal_ports = [
        53,
        80,
        110,
        143,
        443,
        993,
        995,
        3306,
        5432
    ]

    protocols = ["TCP", "UDP"]

    for _ in range(event_count):
        protocol = random.choice(protocols)
        port = random.choice(normal_ports)

        event = create_event(
            source_ip=random_ip(),
            destination_ip=random_ip(),
            protocol=protocol,
            destination_port=port,
            duration=random.uniform(0.2, 5.0),
            packet_size=random.randint(128, 1500),
            connections=random.randint(1, 5),
            scenario="normal"
        )

        events.append(event)

    return events


def port_scan_traffic(event_count: int = 20) -> list[dict]:
    """
    Simula un reconocimiento o Port Scan.

    Una única IP de origen intenta conectarse rápidamente
    a muchos puertos de una misma máquina.

    Características:
    - Misma IP atacante.
    - Misma IP objetivo.
    - Puertos diferentes.
    - Duración muy corta.
    - Paquetes pequeños.
    - Una conexión por intento.
    """

    events = []

    source_ip = random_ip()
    destination_ip = random_ip()

    ports = COMMON_PORTS.copy()
    random.shuffle(ports)

    for index in range(event_count):
        port = ports[index % len(ports)]

        event = create_event(
            source_ip=source_ip,
            destination_ip=destination_ip,
            protocol="TCP",
            destination_port=port,
            duration=random.uniform(0.005, 0.08),
            packet_size=random.randint(40, 90),
            connections=1,
            scenario="port_scan"
        )

        events.append(event)

    return events


def reconnaissance_traffic(event_count: int = 15) -> list[dict]:
    """
    Simula reconocimiento de servicios.

    Es parecido a un Port Scan, pero más lento y variado.
    Se prueban distintos protocolos, hosts y puertos.

    Características:
    - Misma IP de origen.
    - Varios destinos.
    - Diferentes protocolos.
    - Paquetes pequeños.
    - Pocas conexiones.
    """

    events = []

    source_ip = random_ip()
    destination_hosts = [
        random_ip()
        for _ in range(random.randint(2, 5))
    ]

    protocols = ["TCP", "UDP", "ICMP"]

    for _ in range(event_count):
        protocol = random.choice(protocols)

        if protocol == "ICMP":
            destination_port = 0
        else:
            destination_port = random.choice(COMMON_PORTS)

        event = create_event(
            source_ip=source_ip,
            destination_ip=random.choice(destination_hosts),
            protocol=protocol,
            destination_port=destination_port,
            duration=random.uniform(0.02, 0.4),
            packet_size=random.randint(40, 160),
            connections=random.randint(1, 3),
            scenario="reconnaissance"
        )

        events.append(event)

    return events


def dos_traffic(event_count: int = 100) -> list[dict]:
    """
    Simula un ataque DoS sin enviar tráfico real.

    Una IP genera una cantidad elevada de conexiones
    hacia un mismo destino y puerto.

    Características:
    - Misma IP de origen.
    - Misma IP de destino.
    - Mismo puerto.
    - Muchas conexiones.
    - Duraciones mínimas.
    - Paquetes pequeños o medianos.
    """

    events = []

    source_ip = random_ip()
    destination_ip = random_ip()
    target_port = random.choice([80, 443, 8080])

    for _ in range(event_count):
        event = create_event(
            source_ip=source_ip,
            destination_ip=destination_ip,
            protocol="TCP",
            destination_port=target_port,
            duration=random.uniform(0.001, 0.03),
            packet_size=random.randint(40, 250),
            connections=random.randint(200, 1500),
            scenario="dos"
        )

        events.append(event)

    return events


def distributed_dos_traffic(event_count: int = 100) -> list[dict]:
    """
    Simula un comportamiento similar a DDoS.

    Varias IP de origen generan muchas conexiones contra
    un mismo servidor.

    Todo es sintético: no se ejecuta ningún ataque real.
    """

    events = []

    source_ips = [
        random_ip()
        for _ in range(random.randint(5, 15))
    ]

    destination_ip = random_ip()
    target_port = random.choice([80, 443, 8080])

    for _ in range(event_count):
        event = create_event(
            source_ip=random.choice(source_ips),
            destination_ip=destination_ip,
            protocol="TCP",
            destination_port=target_port,
            duration=random.uniform(0.001, 0.04),
            packet_size=random.randint(40, 300),
            connections=random.randint(100, 800),
            scenario="ddos"
        )

        events.append(event)

    return events


def brute_force_traffic(event_count: int = 40) -> list[dict]:
    """
    Simula intentos repetidos de autenticación.

    Una IP intenta conectarse muchas veces al mismo servicio.

    Puede representar intentos contra:
    - SSH
    - FTP
    - RDP
    - PostgreSQL
    - MySQL
    """

    events = []

    source_ip = random_ip()
    destination_ip = random_ip()

    target_services = [
        {
            "port": 21,
            "protocol": "TCP",
            "service": "FTP"
        },
        {
            "port": 22,
            "protocol": "TCP",
            "service": "SSH"
        },
        {
            "port": 3389,
            "protocol": "TCP",
            "service": "RDP"
        },
        {
            "port": 5432,
            "protocol": "TCP",
            "service": "PostgreSQL"
        },
        {
            "port": 3306,
            "protocol": "TCP",
            "service": "MySQL"
        }
    ]

    selected_service = random.choice(target_services)

    for _ in range(event_count):
        event = create_event(
            source_ip=source_ip,
            destination_ip=destination_ip,
            protocol=selected_service["protocol"],
            destination_port=selected_service["port"],
            duration=random.uniform(0.05, 0.8),
            packet_size=random.randint(60, 500),
            connections=random.randint(10, 80),
            scenario="brute_force"
        )

        events.append(event)

    return events


def suspicious_traffic(event_count: int = 20) -> list[dict]:
    """
    Simula comportamientos sospechosos genéricos.

    Combina:
    - Puertos poco comunes.
    - Paquetes muy grandes.
    - Conexiones repetidas.
    - Duraciones inusuales.
    """

    events = []

    suspicious_ports = [
        4444,
        5555,
        6666,
        6667,
        9001,
        31337
    ]

    source_ip = random_ip()

    for _ in range(event_count):
        event = create_event(
            source_ip=source_ip,
            destination_ip=random_ip(),
            protocol=random.choice(["TCP", "UDP"]),
            destination_port=random.choice(suspicious_ports),
            duration=random.uniform(0.01, 12.0),
            packet_size=random.randint(1000, 9000),
            connections=random.randint(10, 200),
            scenario="suspicious"
        )

        events.append(event)

    return events


SCENARIO_GENERATORS: dict[str, Callable[[int], list[dict]]] = {
    "normal": normal_traffic,
    "port_scan": port_scan_traffic,
    "reconnaissance": reconnaissance_traffic,
    "dos": dos_traffic,
    "ddos": distributed_dos_traffic,
    "brute_force": brute_force_traffic,
    "suspicious": suspicious_traffic
}


def get_available_scenarios() -> list[str]:
    """
    Devuelve todos los escenarios disponibles.
    """

    return list(SCENARIO_GENERATORS.keys())


def generate_scenario(
    scenario: str,
    event_count: int
) -> list[dict]:
    """
    Ejecuta el generador correspondiente al escenario indicado.
    """

    normalized_scenario = scenario.strip().lower()

    generator_function = SCENARIO_GENERATORS.get(
        normalized_scenario
    )

    if generator_function is None:
        available = ", ".join(get_available_scenarios())

        raise ValueError(
            f"Escenario no válido: '{scenario}'. "
            f"Escenarios disponibles: {available}"
        )

    if event_count <= 0:
        raise ValueError(
            "La cantidad de eventos debe ser mayor que cero."
        )

    return generator_function(event_count)