from flask import Flask, Response, jsonify, request

from logging_middleware.client import log_event
from notification_app_be.notifications import (
    NotificationServiceError,
    build_priority_snapshot,
    stream_priority_updates,
)
from vehicle_maintanence_scheduling.service import (
    VehicleSchedulingError,
    build_vehicle_schedule_snapshot,
)


app = Flask(__name__)


@app.get("/health")
def healthcheck():
    log_event("backend", "info", "route", "entered healthcheck route")
    payload = {"status": "ok", "service": "affordmed-flask-evaluation"}
    log_event("backend", "info", "route", "exiting healthcheck route")
    return jsonify(payload), 200


@app.get("/api/vehicle-schedule")
def vehicle_schedule():
    log_event("backend", "info", "route", "entered vehicle schedule route")
    try:
        payload = build_vehicle_schedule_snapshot()
        log_event("backend", "info", "route", "exiting vehicle schedule route")
        return jsonify(payload), 200
    except VehicleSchedulingError as exc:
        log_event("backend", "error", "route", str(exc))
        return jsonify({"error": str(exc)}), 502


@app.get("/api/notifications/priority")
def priority_notifications():
    limit = request.args.get("limit", default=10, type=int)
    log_event("backend", "info", "route", "entered priority notifications route")
    try:
        payload = build_priority_snapshot(limit=limit)
        log_event("backend", "info", "route", "exiting priority notifications route")
        return jsonify(payload), 200
    except NotificationServiceError as exc:
        log_event("backend", "error", "route", str(exc))
        return jsonify({"error": str(exc)}), 502


@app.get("/api/notifications/stream")
def notifications_stream():
    limit = request.args.get("limit", default=10, type=int)
    interval = request.args.get("interval", default=15, type=int)
    log_event("backend", "info", "route", "entered notifications stream route")
    try:
        response = Response(
            stream_priority_updates(limit=limit, interval_seconds=interval),
            mimetype="text/event-stream",
        )
        log_event("backend", "info", "route", "exiting notifications stream route")
        return response
    except NotificationServiceError as exc:
        log_event("backend", "error", "route", str(exc))
        return jsonify({"error": str(exc)}), 502


if __name__ == "__main__":
    app.run(debug=False)
