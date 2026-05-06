from logging_middleware import log_event


def solve_knapsack(tasks: list[dict], capacity: int) -> dict:
    log_event("backend", "info", "service", "entered knapsack solver")
    if capacity <= 0:
        log_event("backend", "warn", "service", "received non-positive capacity in knapsack solver")
        log_event("backend", "info", "service", "exiting knapsack solver")
        return {"selectedTaskIDs": [], "totalImpact": 0, "totalDuration": 0}

    dp = [0] * (capacity + 1)
    picks: list[list[str]] = [[] for _ in range(capacity + 1)]
    durations = [0] * (capacity + 1)

    for task in tasks:
        duration = int(task["Duration"])
        impact = int(task["Impact"])
        task_id = task["TaskID"]
        for remaining in range(capacity, duration - 1, -1):
            candidate_impact = dp[remaining - duration] + impact
            candidate_duration = durations[remaining - duration] + duration
            if candidate_impact > dp[remaining]:
                dp[remaining] = candidate_impact
                durations[remaining] = candidate_duration
                picks[remaining] = picks[remaining - duration] + [task_id]

    best_capacity = max(range(capacity + 1), key=lambda item: (dp[item], durations[item]))
    result = {
        "selectedTaskIDs": picks[best_capacity],
        "totalImpact": dp[best_capacity],
        "totalDuration": durations[best_capacity],
    }
    log_event("backend", "info", "service", "exiting knapsack solver")
    return result
