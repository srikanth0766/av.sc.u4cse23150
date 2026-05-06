## Stage 1

### Core actions

- Fetch notifications for a student inbox
- Fetch unread notifications only
- Mark one notification as read
- Mark all notifications as read
- Create a notification for one or many students
- Subscribe to live notification updates

### REST API contract

`GET /api/notifications`

- Headers: `Authorization: Bearer <token>`
- Query params: `studentId` required, `isRead` optional, `type` optional, `limit` optional, `cursor` optional
- Response `200`:

```json
{
  "items": [
    {
      "id": "uuid",
      "studentId": 1042,
      "type": "Placement",
      "message": "CSX Corporation hiring",
      "isRead": false,
      "createdAt": "2026-04-22T17:51:18Z"
    }
  ],
  "nextCursor": "opaque-cursor"
}
```

`PATCH /api/notifications/{notificationId}/read`

- Headers: `Authorization: Bearer <token>`
- Body:

```json
{
  "isRead": true
}
```

- Response `200`:

```json
{
  "id": "uuid",
  "isRead": true,
  "readAt": "2026-05-06T10:30:00Z"
}
```

`PATCH /api/notifications/read-all`

- Headers: `Authorization: Bearer <token>`
- Body:

```json
{
  "studentId": 1042
}
```

- Response `200`:

```json
{
  "studentId": 1042,
  "updatedCount": 37
}
```

`POST /api/notifications`

- Headers: `Authorization: Bearer <token>`
- Body:

```json
{
  "type": "Placement",
  "message": "AMD hiring drive",
  "recipientStudentIds": [1042, 1099]
}
```

- Response `202`:

```json
{
  "jobId": "uuid",
  "status": "queued"
}
```

### Status codes

- `200` successful read/update
- `202` accepted for async bulk send
- `400` validation failure
- `401` invalid token
- `403` unauthorized caller
- `404` notification not found
- `429` rate limited
- `500` internal server error

### Real-time delivery choice

Server-Sent Events is a strong fit for the student inbox because the client mainly needs one-way server-to-browser updates, reconnection is simple, and the transport is lighter than full WebSockets. Use `GET /api/notifications/stream?studentId=1042` returning `text/event-stream`.

## Stage 2

### Storage choice

Use PostgreSQL. The workload has clear relational entities, strong consistency needs for read-state, and benefits from transactional writes for inbox records plus mature indexing and partitioning.

### Schema

```sql
CREATE TYPE notification_type AS ENUM ('Event', 'Result', 'Placement');

CREATE TABLE students (
    id BIGINT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    type notification_type NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE notification_recipients (
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMPTZ NULL,
    delivered_in_app_at TIMESTAMPTZ NULL,
    emailed_at TIMESTAMPTZ NULL,
    PRIMARY KEY (notification_id, student_id)
);

CREATE INDEX idx_recipients_student_unread_created
ON notification_recipients (student_id, is_read, notification_id);

CREATE INDEX idx_notifications_created
ON notifications (created_at DESC);

CREATE INDEX idx_notifications_type_created
ON notifications (type, created_at DESC);
```

### Scale issues and mitigations

- Large unread inbox scans become slow without composite indexes.
- Hot students can create index and cache pressure.
- Bulk fanout creates write spikes and lock contention.
- Table size grows quickly, so partition `notifications` by time and archive old rows.
- Use cursor pagination instead of offsets.
- Move bulk delivery work to queues and workers.

### Query mapping

```sql
SELECT n.id, nr.student_id, n.type, n.message, nr.is_read, n.created_at
FROM notification_recipients nr
JOIN notifications n ON n.id = nr.notification_id
WHERE nr.student_id = $1
  AND ($2::BOOLEAN IS NULL OR nr.is_read = $2)
  AND ($3::notification_type IS NULL OR n.type = $3)
ORDER BY n.created_at DESC
LIMIT $4;
```

```sql
UPDATE notification_recipients
SET is_read = TRUE, read_at = NOW()
WHERE notification_id = $1 AND student_id = $2;
```

## Stage 3

The query is incomplete if unread state is stored per-recipient in a join table rather than directly in `notifications`. It is slow because `SELECT *` fetches excess columns, the filter can hit many rows, and `ORDER BY createdAt DESC` forces sorting unless a matching composite index exists.

Use a recipient table and a composite index that matches the access pattern:

```sql
CREATE INDEX idx_recipient_unread_created
ON notification_recipients (student_id, is_read, notification_id);

CREATE INDEX idx_notification_created
ON notifications (created_at DESC);
```

Then query:

```sql
SELECT n.id, n.type, n.message, n.created_at
FROM notification_recipients nr
JOIN notifications n ON n.id = nr.notification_id
WHERE nr.student_id = 1042
  AND nr.is_read = FALSE
ORDER BY n.created_at DESC;
```

Likely cost after the fix is near index-range-scan plus ordered join work for one student's unread subset, which is dramatically smaller than scanning millions of rows.

Adding indexes on every column is not effective. Extra indexes increase write cost, storage, vacuum overhead, and planner complexity. Indexes should be driven by real query patterns and selectivity.

Students who received a placement notification in the last 7 days:

```sql
SELECT DISTINCT nr.student_id
FROM notification_recipients nr
JOIN notifications n ON n.id = nr.notification_id
WHERE n.type = 'Placement'
  AND n.created_at >= NOW() - INTERVAL '7 days';
```

## Stage 4

Reduce DB load with a layered approach:

- Cache the first inbox page and unread count in Redis per student.
- Invalidate or patch the cache on new notification fanout and read-state updates.
- Use SSE so clients do not poll repeatedly.
- Precompute priority-inbox slices for frequently opened views.

This improves performance by shifting repeated reads from the database to memory and by replacing wasteful page-load polling with push updates.

Tradeoffs:

- Redis adds operational complexity and memory cost.
- Cached inboxes can be briefly stale.
- Invalidation is harder than read-through caching for immutable data.
- Precomputed views reduce latency but increase write-path work.

## Stage 5

The proposed loop is slow, serial, and fragile. A single email API slowdown delays everyone, partial failure handling is poor, and the workflow has no idempotency or retry control.

If `send_email` failed for 200 students midway, do not rerun the whole batch blindly. Persist a delivery job, mark per-student attempt status, and retry only the failed email tasks with backoff and idempotency keys.

Saving to DB and sending email should not be one atomic distributed step. The database should be the source of truth first, then downstream delivery should happen asynchronously from durable queued work. Trying to make DB and email one atomic transaction is impractical because the email provider is an external side effect.

Revised pseudocode:

```text
function notify_all(student_ids, message, type):
    notification_id = insert_notification(type, message)
    bulk_insert_recipients(notification_id, student_ids)
    enqueue_fanout_job(notification_id)

worker process fanout_job(notification_id):
    recipients = fetch_pending_recipients(notification_id)
    for recipient in recipients:
        enqueue_email_task(notification_id, recipient.student_id)
        enqueue_push_task(notification_id, recipient.student_id)

worker process email_task(notification_id, student_id):
    if already_emailed(notification_id, student_id):
        return
    send_email(student_id, notification_id)
    mark_emailed(notification_id, student_id)

worker process push_task(notification_id, student_id):
    push_to_app(student_id, notification_id)
    mark_pushed(notification_id, student_id)
```

## Stage 6

Priority Inbox ranks unread notifications by type weight first and timestamp second. In code, `Placement = 3`, `Result = 2`, and `Event = 1`. The Flask build fetches live data from `GET /notifications`, then keeps only the top `N` items using a min-heap, so it avoids fully resorting the stream on every update.

For live updates, maintain a bounded heap of size `N`. When a new notification arrives, compare its `(weight, timestamp)` rank against the heap minimum:

- If the heap is not full, push it.
- If it outranks the minimum, replace the minimum.
- Otherwise ignore it for the current top `N`.

This gives `O(log N)` update cost per incoming notification after the initial load.
