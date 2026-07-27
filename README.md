# intervals-icu-client

Shared Python client for the [Intervals.icu](https://intervals.icu) API.

Used by:
- [training-coach-agent](https://github.com/eloyrgz/training-coach-agent) — sync pipeline, coach tools
- [eighty-twenty-plan-generator](https://github.com/eloyrgz/eighty-twenty-plan-generator) — plan push, workout matching

## Installation

```bash
pip install git+https://github.com/eloyrgz/intervals-icu-client.git
```

## Usage

```python
from intervals_icu_client import IntervalsClient

client = IntervalsClient(athlete_id="i87571", api_key="your_api_key")

# Fetch activities
activities = client.get_activities(oldest="2026-01-01", newest="2026-07-27")

# Fetch scheduled events
events = client.get_events(oldest="2026-07-28", newest="2026-08-03")

# Push plan events to calendar
client.create_events_bulk([
    {
        "start_date_local": "2026-08-01",
        "category": "WORKOUT",
        "name": "Easy Run 45min",
        "moving_time": 2700,
        "external_id": "plan_1_w1_Tue",
    }
])

# Update activity RPE
client.update_activity("12345", {"icu_rpe": 7})

# Post a comment on an activity
client.post_activity_message("12345", "Felt great today!")

# List workout library
workouts = client.get_workouts()
```

## API Coverage

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `get_activities(oldest, newest)` | GET /athlete/{id}/activities | Fetch activity history |
| `update_activity(id, data)` | PUT /activity/{id} | Update RPE, notes, etc. |
| `post_activity_message(id, msg)` | POST /activity/{id}/messages | Add comment |
| `get_events(oldest, newest)` | GET /athlete/{id}/events | Calendar events |
| `create_events_bulk(events)` | POST /athlete/{id}/events/bulk | Push planned workouts |
| `delete_events_bulk(ext_ids)` | PUT /athlete/{id}/events/bulk-delete | Remove by external_id |
| `delete_event(event_id)` | DELETE /athlete/{id}/events/{id} | Remove single event |
| `get_workouts()` | GET /athlete/{id}/workouts | Workout library |
| `get_workout(id)` | GET /athlete/{id}/workouts/{id} | Single workout detail |
| `create_workout(data)` | POST /athlete/{id}/workouts | Add to library |

## Environment

The client itself does not read environment variables — pass credentials explicitly.
Your calling code typically loads from `.env`:

```python
import os
from dotenv import load_dotenv
from intervals_icu_client import IntervalsClient

load_dotenv()
client = IntervalsClient(
    athlete_id=os.getenv("INTERVALS_ATHLETE_ID"),
    api_key=os.getenv("INTERVALS_API_KEY"),
)
```
