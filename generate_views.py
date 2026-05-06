import json
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VEHICLE_OUTPUT = ROOT / "vehicle_maintanence_scheduling" / "output.json"
VEHICLE_HTML = ROOT / "vehicle_maintanence_scheduling" / "output.html"
NOTIFICATION_OUTPUT = ROOT / "notification_app_be" / "output.json"
NOTIFICATION_HTML = ROOT / "notification_app_be" / "output.html"


def _page_shell(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)}</title>
  <style>
    :root {{
      --bg: #f5f7fb;
      --card: #ffffff;
      --ink: #132238;
      --muted: #5f6f84;
      --accent: #0f766e;
      --accent-2: #d97706;
      --line: #d9e2ec;
      --chip: #eef6ff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(15,118,110,0.12), transparent 28%),
        linear-gradient(180deg, #f8fbff 0%, var(--bg) 100%);
      color: var(--ink);
      padding: 32px;
    }}
    .wrap {{
      max-width: 1180px;
      margin: 0 auto;
    }}
    .hero {{
      background: linear-gradient(135deg, #0f172a 0%, #123047 55%, #0f766e 100%);
      color: white;
      border-radius: 26px;
      padding: 28px 32px;
      box-shadow: 0 24px 70px rgba(15, 23, 42, 0.18);
    }}
    h1 {{
      margin: 0 0 8px 0;
      font-size: 42px;
      line-height: 1.05;
    }}
    .subtitle {{
      margin: 0;
      font-size: 18px;
      color: rgba(255,255,255,0.82);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
      margin-top: 22px;
    }}
    .stat, .card {{
      background: var(--card);
      border: 1px solid rgba(217, 226, 236, 0.9);
      border-radius: 22px;
      box-shadow: 0 14px 38px rgba(15, 23, 42, 0.06);
    }}
    .stat {{
      padding: 20px 22px;
    }}
    .label {{
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 8px;
    }}
    .value {{
      font-size: 32px;
      font-weight: 700;
    }}
    .cards {{
      display: grid;
      gap: 18px;
      margin-top: 22px;
    }}
    .card {{
      padding: 22px;
    }}
    .card-head {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      margin-bottom: 16px;
    }}
    h2 {{
      margin: 0;
      font-size: 27px;
    }}
    .meta {{
      color: var(--muted);
      font-size: 15px;
    }}
    .chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 14px;
    }}
    .chip {{
      background: var(--chip);
      color: #15467a;
      border: 1px solid #cfe0f5;
      border-radius: 999px;
      padding: 8px 12px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
    }}
    th, td {{
      text-align: left;
      padding: 14px 12px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }}
    th {{
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .tag {{
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      color: white;
      font-weight: 700;
      font-size: 12px;
    }}
    .placement {{ background: #0f766e; }}
    .result {{ background: #1d4ed8; }}
    .event {{ background: #d97706; }}
  </style>
</head>
<body>
  <div class="wrap">
    {body}
  </div>
</body>
</html>
"""


def build_vehicle_html() -> None:
    payload = json.loads(VEHICLE_OUTPUT.read_text(encoding="utf-8"))
    stats = f"""
    <div class="hero">
      <h1>Vehicle Maintenance Scheduler</h1>
      <p class="subtitle">Live output from the Affordmed evaluation service rendered for submission screenshots.</p>
    </div>
    <div class="grid">
      <div class="stat"><div class="label">Depots Processed</div><div class="value">{payload['depotsProcessed']}</div></div>
      <div class="stat"><div class="label">Tasks Available</div><div class="value">{payload['tasksAvailable']}</div></div>
      <div class="stat"><div class="label">Best Total Impact</div><div class="value">{max(item['totalImpact'] for item in payload['schedules'])}</div></div>
    </div>
    """

    cards = []
    for schedule in payload["schedules"]:
        chips = "".join(
            f'<span class="chip">{escape(task_id)}</span>'
            for task_id in schedule["selectedTaskIDs"]
        )
        cards.append(
            f"""
            <section class="card">
              <div class="card-head">
                <h2>Depot {schedule['depotID']}</h2>
                <div class="meta">Capacity {schedule['mechanicHours']} hrs • Used {schedule['totalDuration']} hrs • Impact {schedule['totalImpact']}</div>
              </div>
              <div class="chips">{chips}</div>
            </section>
            """
        )

    VEHICLE_HTML.write_text(
        _page_shell(
            "Vehicle Maintanence Scheduling Output",
            stats + '<div class="cards">' + "".join(cards) + "</div>",
        ),
        encoding="utf-8",
    )


def build_notification_html() -> None:
    payload = json.loads(NOTIFICATION_OUTPUT.read_text(encoding="utf-8"))
    rows = []
    for index, item in enumerate(payload["topNotifications"], start=1):
        tag_class = item["Type"].lower()
        rows.append(
            f"""
            <tr>
              <td>{index}</td>
              <td><span class="tag {tag_class}">{escape(item['Type'])}</span></td>
              <td>{escape(item['Message'])}</td>
              <td><code>{escape(item['ID'])}</code></td>
              <td>{escape(item['Timestamp'])}</td>
            </tr>
            """
        )

    body = f"""
    <div class="hero">
      <h1>Priority Inbox Output</h1>
      <p class="subtitle">Top {payload['limit']} notifications ranked by type weight and recency from the live notifications API.</p>
    </div>
    <div class="grid">
      <div class="stat"><div class="label">Priority Limit</div><div class="value">{payload['limit']}</div></div>
      <div class="stat"><div class="label">Fetched Notifications</div><div class="value">{payload['totalNotifications']}</div></div>
      <div class="stat"><div class="label">Highest Type Weight</div><div class="value">3</div></div>
    </div>
    <section class="card" style="margin-top: 22px;">
      <div class="card-head">
        <h2>Top Notifications</h2>
        <div class="meta">Placement &gt; Result &gt; Event, then newest first</div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Type</th>
            <th>Message</th>
            <th>ID</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </section>
    """

    NOTIFICATION_HTML.write_text(_page_shell("Priority Inbox Output", body), encoding="utf-8")


def main() -> None:
    build_vehicle_html()
    build_notification_html()


if __name__ == "__main__":
    main()
