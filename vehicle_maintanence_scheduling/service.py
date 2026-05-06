import json
from urllib import error

from logging_middleware.client import _send_json, BASE_URL, log_event
from vehicle_maintanence_scheduling.solver import solve_knapsack


DEPOTS_URL = f"{BASE_URL}/depots"
VEHICLES_URL = f"{BASE_URL}/vehicles"


class VehicleSchedulingError(Exception):
    pass


def _fetch_depots() -> list[dict]:
    log_event("backend", "info", "service", "fetching depots")
    try:
        payload = _send_json(DEPOTS_URL)
    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        log_event("backend", "error", "service", f"failed to fetch depots: {exc}")
        raise VehicleSchedulingError(f"failed to fetch depots: {exc}") from exc
    depots = payload.get("depots")
    if not isinstance(depots, list):
        log_event("backend", "error", "service", "depots response missing depots list")
        raise VehicleSchedulingError("depots response missing depots list")
    log_event("backend", "info", "service", "fetched depots")
    return depots


def _fetch_vehicles() -> list[dict]:
    log_event("backend", "info", "service", "fetching vehicles")
    try:
        payload = _send_json(VEHICLES_URL)
    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        log_event("backend", "error", "service", f"failed to fetch vehicles: {exc}")
        raise VehicleSchedulingError(f"failed to fetch vehicles: {exc}") from exc
    vehicles = payload.get("vehicles")
    if not isinstance(vehicles, list):
        log_event("backend", "error", "service", "vehicles response missing vehicles list")
        raise VehicleSchedulingError("vehicles response missing vehicles list")
    log_event("backend", "info", "service", "fetched vehicles")
    return vehicles


def build_vehicle_schedule_snapshot() -> dict:
    log_event("backend", "info", "service", "entered build vehicle schedule snapshot")
    try:
        depots = _fetch_depots()
        vehicles = _fetch_vehicles()

        schedules = []
        for depot in depots:
            depot_id = depot["ID"]
            capacity = int(depot["MechanicHours"])
            log_event("backend", "info", "service", f"computing schedule for depot {depot_id}")
            schedule = solve_knapsack(vehicles, capacity)
            schedules.append(
                {
                    "depotID": depot_id,
                    "mechanicHours": capacity,
                    **schedule,
                }
            )
            log_event("backend", "info", "service", f"computed schedule for depot {depot_id}")

        result = {
            "depotsProcessed": len(depots),
            "tasksAvailable": len(vehicles),
            "schedules": schedules,
        }
        log_event("backend", "info", "service", "exiting build vehicle schedule snapshot")
        return result
    except VehicleSchedulingError as exc:
        log_event("backend", "error", "service", str(exc))
        raise
