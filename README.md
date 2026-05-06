# Affordmed Flask Evaluation Build

This project implements the backend evaluation using Flask and the Python standard library only, with reusable logging middleware, a vehicle maintenance scheduler, and the Stage 6 priority inbox logic.

## Run

```bash
export EVAL_ACCESS_TOKEN="paste-a-fresh-bearer-token-here"
venv/bin/flask --app app run
```

Live API calls require a fresh bearer token. Set `EVAL_ACCESS_TOKEN` in your shell before generating outputs.

## Endpoints

- `GET /health`
- `GET /api/vehicle-schedule`
- `GET /api/notifications/priority?limit=10`
- `GET /api/notifications/stream?limit=10&interval=15`

## Deliverable folders

- `logging_middleware/`: reusable log client
- `vehicle_maintanence_scheduling/`: scheduler code, output JSON, HTML view, and screenshot
- `notification_app_be/`: priority inbox code, output JSON, HTML view, and screenshot
- `notification_system_design.md`: Stages 1 through 6 writeup

## Generated artifacts

- Vehicle scheduler JSON: [vehicle_maintanence_scheduling/output.json](/Users/ramkey03/Desktop/test/vehicle_maintanence_scheduling/output.json)
- Vehicle scheduler screenshot: [vehicle_maintanence_scheduling/vehicle_maintanence_scheduling_screenshot.png](/Users/ramkey03/Desktop/test/vehicle_maintanence_scheduling/vehicle_maintanence_scheduling_screenshot.png)
- Priority inbox JSON: [notification_app_be/output.json](/Users/ramkey03/Desktop/test/notification_app_be/output.json)
- Priority inbox screenshot: [notification_app_be/priority_notifications_screenshot.png](/Users/ramkey03/Desktop/test/notification_app_be/priority_notifications_screenshot.png)

## Notes

- All outbound API calls include the required bearer token.
- The reusable log client lives in `logging_middleware/client.py`.
- No database is used; all scheduling and priority calculations run in memory.
