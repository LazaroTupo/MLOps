from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    scenario: str = Field(
        min_length=2,
        max_length=50,
        examples=["port_scan"]
    )

    duration: int = Field(
        default=30,
        ge=1,
        le=3600,
        description="Duración de la simulación en segundos."
    )


class GenerateRequest(BaseModel):
    scenario: str = Field(
        min_length=2,
        max_length=50,
        examples=["brute_force"]
    )

    events: int = Field(
        ge=1,
        le=10000,
        description="Cantidad exacta de eventos que se generarán."
    )


class StatusResponse(BaseModel):
    running: bool
    scenario: str | None
    generated_events: int
    simulation_id: int | None


class TrafficRecord(BaseModel):
    source_ip: str
    destination_ip: str
    protocol: str
    destination_port: int
    duration: float
    packet_size: int
    connections: int
    scenario: str