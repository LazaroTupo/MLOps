from fastapi import FastAPI, HTTPException, status

import simulator
from database import check_database_connection
from models import GenerateRequest, SimulationRequest
from scenarios import get_available_scenarios


app = FastAPI(
    title="SoftInt Traffic Generator API",
    description=(
        "API para generar eventos sintéticos de tráfico normal "
        "y anómalo sin realizar ataques reales."
    ),
    version="1.0.0"
)


@app.get("/")
def home() -> dict:
    return {
        "service": "SoftInt Traffic Generator",
        "status": "running",
        "documentation": "/docs"
    }


@app.get("/health")
def health() -> dict:
    database_available = check_database_connection()

    if not database_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL no está disponible."
        )

    return {
        "service": "traffic_generator",
        "status": "healthy",
        "database": "connected"
    }


@app.get("/scenarios")
def scenarios() -> dict:
    return {
        "available_scenarios": get_available_scenarios()
    }


@app.post(
    "/simulate",
    status_code=status.HTTP_202_ACCEPTED
)
def simulate(request: SimulationRequest) -> dict:
    scenario = request.scenario.strip().lower()

    if scenario not in get_available_scenarios():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Escenario no válido: {scenario}",
                "available_scenarios": get_available_scenarios()
            }
        )

    if request.duration <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La duración debe ser mayor que cero."
        )

    if request.duration > 3600:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La duración máxima es de 3600 segundos."
        )

    try:
        result = simulator.start_simulation(
            scenario=scenario,
            duration=request.duration
        )

        return result

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        ) from error


@app.post("/generate")
def generate(request: GenerateRequest) -> dict:
    scenario = request.scenario.strip().lower()

    if scenario not in get_available_scenarios():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Escenario no válido: {scenario}",
                "available_scenarios": get_available_scenarios()
            }
        )

    if request.events <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cantidad de eventos debe ser mayor que cero."
        )

    if request.events > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden generar hasta 10000 eventos por solicitud."
        )

    try:
        generated = simulator.generate_fixed_events(
            scenario=scenario,
            event_count=request.events
        )

        return {
            "message": "Eventos generados correctamente.",
            "scenario": scenario,
            "generated_events": generated
        }

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        ) from error


@app.post("/stop")
def stop() -> dict:
    stopped = simulator.stop_simulation()

    if not stopped:
        return {
            "message": "No existe una simulación activa.",
            "running": False
        }

    return {
        "message": "Se solicitó detener la simulación.",
        "running": False
    }


@app.get("/status")
def simulation_status() -> dict:
    return simulator.get_status()