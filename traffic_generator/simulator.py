import threading
import time
from typing import Any

from config import DEFAULT_EVENTS_PER_SECOND
from database import (
    create_simulation,
    finish_simulation,
    insert_events
)
from scenarios import (
    generate_scenario,
    get_available_scenarios
)


_state_lock = threading.Lock()
_stop_event = threading.Event()

_simulation_thread: threading.Thread | None = None

_running = False
_generated_events = 0
_current_scenario: str | None = None
_current_simulation_id: int | None = None
_started_at: float | None = None


def _simulation_worker(
    scenario: str,
    duration: int,
    simulation_id: int
) -> None:
    global _running
    global _generated_events
    global _current_scenario
    global _current_simulation_id
    global _started_at

    final_status = "COMPLETED"

    try:
        start_time = time.time()

        while not _stop_event.is_set():
            elapsed = time.time() - start_time

            if elapsed >= duration:
                break

            events = generate_scenario(
                scenario=scenario,
                event_count=DEFAULT_EVENTS_PER_SECOND
            )

            inserted = insert_events(events)

            with _state_lock:
                _generated_events += inserted

            remaining_second = 1.0 - (
                time.time() - start_time - elapsed
            )

            if remaining_second > 0:
                _stop_event.wait(remaining_second)

        if _stop_event.is_set():
            final_status = "STOPPED"

    except Exception as error:
        final_status = "FAILED"
        print(
            f"Error durante la simulación "
            f"{simulation_id}: {error}"
        )

    finally:
        with _state_lock:
            final_generated = _generated_events

        try:
            finish_simulation(
                simulation_id=simulation_id,
                status=final_status,
                generated_events=final_generated
            )

        except Exception as error:
            print(
                "No se pudo actualizar el estado final "
                f"de la simulación: {error}"
            )

        with _state_lock:
            _running = False
            _current_scenario = None
            _current_simulation_id = None
            _started_at = None

        _stop_event.clear()


def start_simulation(
    scenario: str,
    duration: int
) -> dict[str, Any]:
    global _running
    global _generated_events
    global _current_scenario
    global _current_simulation_id
    global _started_at
    global _simulation_thread

    normalized_scenario = scenario.strip().lower()

    if normalized_scenario not in get_available_scenarios():
        raise ValueError(
            f"Escenario no válido: {scenario}"
        )

    if duration <= 0:
        raise ValueError(
            "La duración debe ser mayor que cero."
        )

    with _state_lock:
        if _running:
            raise RuntimeError(
                "Ya existe una simulación en ejecución."
            )

        simulation_id = create_simulation(
            scenario=normalized_scenario,
            requested_duration=duration
        )

        _running = True
        _generated_events = 0
        _current_scenario = normalized_scenario
        _current_simulation_id = simulation_id
        _started_at = time.time()

        _stop_event.clear()

        _simulation_thread = threading.Thread(
            target=_simulation_worker,
            args=(
                normalized_scenario,
                duration,
                simulation_id
            ),
            daemon=True,
            name=f"simulation-{simulation_id}"
        )

        _simulation_thread.start()

    return {
        "message": "Simulación iniciada.",
        "simulation_id": simulation_id,
        "scenario": normalized_scenario,
        "duration": duration,
        "events_per_second": DEFAULT_EVENTS_PER_SECOND
    }


def stop_simulation() -> bool:
    with _state_lock:
        if not _running:
            return False

    _stop_event.set()

    return True


def generate_fixed_events(
    scenario: str,
    event_count: int
) -> int:
    normalized_scenario = scenario.strip().lower()

    if normalized_scenario not in get_available_scenarios():
        raise ValueError(
            f"Escenario no válido: {scenario}"
        )

    if event_count <= 0:
        raise ValueError(
            "La cantidad de eventos debe ser mayor que cero."
        )

    total_inserted = 0
    batch_size = 100
    remaining = event_count

    while remaining > 0:
        current_batch_size = min(
            batch_size,
            remaining
        )

        generated = generate_scenario(
            scenario=normalized_scenario,
            event_count=current_batch_size
        )

        inserted = insert_events(generated)

        total_inserted += inserted
        remaining -= inserted

    return total_inserted


def get_status() -> dict[str, Any]:
    with _state_lock:
        elapsed_seconds = None

        if _running and _started_at is not None:
            elapsed_seconds = round(
                time.time() - _started_at,
                2
            )

        return {
            "running": _running,
            "scenario": _current_scenario,
            "generated_events": _generated_events,
            "simulation_id": _current_simulation_id,
            "elapsed_seconds": elapsed_seconds,
            "events_per_second": DEFAULT_EVENTS_PER_SECOND
        }