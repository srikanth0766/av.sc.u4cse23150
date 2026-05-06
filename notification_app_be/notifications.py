import json
import time
from datetime import datetime
from heapq import heappush, heappushpop
from urllib import error

from logging_middleware.client import _send_json, BASE_URL, log_event


NOTIFICATIONS_URL = f"{BASE_URL}/notifications"
TYPE_WEIGHT = {"Placement": 3, "Result": 2, "Event": 1}


class NotificationServiceError(Exception):
    pass


def _parse_timestamp(timestamp: str) -> datetime:
    log_event("backend", "info", "service", "parsing notification timestamp")
    try:
        parsed = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        log_event("backend", "info", "service", "parsed notification timestamp")
        return parsed
    except ValueError as exc:
        log_event("backend", "error", "service", f"failed to parse notification timestamp: {exc}")
        raise NotificationServiceError(f"failed to parse notification timestamp: {exc}") from exc


def _fetch_notifications() -> list[dict]:
    log_event("backend", "info", "service", "fetching notifications")
    try:
        payload = _send_json(NOTIFICATIONS_URL)
    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        log_event("backend", "error", "service", f"failed to fetch notifications: {exc}")
        raise NotificationServiceError(f"failed to fetch notifications: {exc}") from exc
    notifications = payload.get("notifications")
    if not isinstance(notifications, list):
        log_event("backend", "error", "service", "notifications response missing notifications list")
        raise NotificationServiceError("notifications response missing notifications list")
    log_event("backend", "info", "service", "fetched notifications")
    return notifications


def _notification_rank(notification: dict) -> tuple[int, datetime]:
    log_event("backend", "info", "service", "computing notification rank")
    try:
        rank = (
            TYPE_WEIGHT.get(notification["Type"], 0),
            _parse_timestamp(notification["Timestamp"]),
        )
        log_event("backend", "info", "service", "computed notification rank")
        return rank
    except KeyError as exc:
        log_event("backend", "error", "service", f"notification missing rank field: {exc}")
        raise NotificationServiceError(f"notification missing rank field: {exc}") from exc


def top_notifications(notifications: list[dict], limit: int) -> list[dict]:
    log_event("backend", "info", "service", "computing priority notifications")
    if limit <= 0:
        log_event("backend", "warn", "service", "received non-positive priority notification limit")
        log_event("backend", "info", "service", "computed priority notifications")
        return []

    heap: list[tuple[tuple[int, datetime], str, dict]] = []
    for notification in notifications:
        rank = _notification_rank(notification)
        item = (rank, notification["ID"], notification)
        if len(heap) < limit:
            heappush(heap, item)
        else:
            heappushpop(heap, item)

    ordered = [entry[2] for entry in sorted(heap, key=lambda item: (item[0], item[1]), reverse=True)]
    log_event("backend", "info", "service", "computed priority notifications")
    return ordered


def build_priority_snapshot(limit: int = 10) -> dict:
    log_event("backend", "info", "service", "entered build priority snapshot")
    try:
        notifications = _fetch_notifications()
        top = top_notifications(notifications, limit=limit)
        snapshot = {
            "limit": limit,
            "totalNotifications": len(notifications),
            "topNotifications": top,
        }
        log_event("backend", "info", "service", "exiting build priority snapshot")
        return snapshot
    except NotificationServiceError as exc:
        log_event("backend", "error", "service", str(exc))
        raise


def stream_priority_updates(limit: int = 10, interval_seconds: int = 15):
    log_event("backend", "info", "service", "entered stream priority updates")
    previous_signature = None
    while True:
        try:
            snapshot = build_priority_snapshot(limit=limit)
            signature = json.dumps(snapshot["topNotifications"], sort_keys=True)
            if signature != previous_signature:
                log_event("backend", "info", "service", "streaming priority notification update")
                yield f"data: {json.dumps(snapshot)}\n\n"
                previous_signature = signature
        except NotificationServiceError as exc:
            log_event("backend", "warn", "service", str(exc))
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
        time.sleep(max(interval_seconds, 1))
