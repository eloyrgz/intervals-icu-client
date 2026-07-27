"""Intervals.icu API client.

Uses HTTP Basic auth with username "API_KEY" and password = the athlete's
Intervals.icu API key, per https://forum.intervals.icu/t/api-access-to-intervals-icu/609

Covers read/write endpoints needed by:
- training-coach-agent (sync_pipeline, coach_tools)
- eighty-twenty-plan-generator (workout matching, plan push)

No credentials are logged or persisted.
"""
from __future__ import annotations

import requests
from typing import Any

from .exceptions import IntervalsAPIError

BASE_URL = "https://intervals.icu"

# Cloudflare in front of intervals.icu can challenge default user agents.
_USER_AGENT = (
    "Mozilla/5.0 (compatible; intervals-icu-client/0.1; "
    "+https://github.com/eloyrgz/intervals-icu-client)"
)

_DEFAULT_TIMEOUT = 30


class IntervalsClient:
    """Intervals.icu API client.

    Args:
        athlete_id: Intervals.icu athlete ID (e.g. "i87571").
        api_key: Intervals.icu API key.
        timeout: Request timeout in seconds (default 30).
    """

    def __init__(self, athlete_id: str, api_key: str, timeout: int = _DEFAULT_TIMEOUT):
        self.athlete_id = athlete_id
        self.api_key = api_key
        self.timeout = timeout
        self._session = requests.Session()
        self._session.auth = ("API_KEY", api_key)
        self._session.headers.update({
            "User-Agent": _USER_AGENT,
            "Accept": "application/json",
        })

    # ------------------------------------------------------------------
    # Activities
    # ------------------------------------------------------------------

    def get_activities(self, oldest: str, newest: str) -> list[dict]:
        """Fetch activities in a date range.

        Args:
            oldest: Start date (YYYY-MM-DD).
            newest: End date (YYYY-MM-DD).

        Returns list of activity dicts with id, start_date_local, name, type,
        distance, moving_time, total_elevation_gain, icu_rpe, icu_training_load,
        icu_ctl, icu_atl, developer_text, description, etc.
        """
        return self._get(
            f"/api/v1/athlete/{self.athlete_id}/activities",
            params={"oldest": oldest, "newest": newest},
        )

    def update_activity(self, activity_id: str | int, data: dict) -> dict:
        """Update an activity's fields (e.g. icu_rpe).

        Args:
            activity_id: The Intervals.icu activity ID.
            data: Dict of fields to update.
        """
        return self._put(f"/api/v1/activity/{activity_id}", json=data)

    def post_activity_message(self, activity_id: str | int, message: str) -> dict:
        """Post a comment/message on an activity.

        Args:
            activity_id: The Intervals.icu activity ID.
            message: Comment text.
        """
        return self._post(
            f"/api/v1/activity/{activity_id}/messages",
            json={"message": message},
        )

    # ------------------------------------------------------------------
    # Events (calendar: planned workouts, notes, races)
    # ------------------------------------------------------------------

    def get_events(self, oldest: str, newest: str, category: str | None = None) -> list[dict]:
        """Fetch calendar events in a date range.

        Args:
            oldest: Start date (YYYY-MM-DD).
            newest: End date (YYYY-MM-DD).
            category: Optional filter (WORKOUT, NOTE, RACE, etc.).
        """
        params: dict[str, str] = {"oldest": oldest, "newest": newest}
        if category:
            params["category"] = category
        return self._get(f"/api/v1/athlete/{self.athlete_id}/events", params=params)

    def create_events_bulk(
        self,
        events: list[dict],
        *,
        upsert: bool = True,
        update_plan_applied: bool = False,
    ) -> list[dict]:
        """Create/update multiple calendar events in one call.

        Args:
            events: List of event dicts (start_date_local, category, name, etc.).
            upsert: If True, updates existing events with matching external_id.
            update_plan_applied: Whether to mark plan as applied.
        """
        query = f"upsert={'true' if upsert else 'false'}&updatePlanApplied={'true' if update_plan_applied else 'false'}"
        return self._post(
            f"/api/v1/athlete/{self.athlete_id}/events/bulk?{query}",
            json=events,
        )

    def delete_events_bulk(self, external_ids: list[str]) -> dict:
        """Delete events by external_id.

        Args:
            external_ids: List of external IDs to match for deletion.
        """
        body = [{"external_id": ext_id} for ext_id in external_ids]
        return self._put(
            f"/api/v1/athlete/{self.athlete_id}/events/bulk-delete",
            json=body,
        )

    def delete_event(self, event_id: int | str) -> dict:
        """Delete a single calendar event by its Intervals.icu event id."""
        return self._delete(f"/api/v1/athlete/{self.athlete_id}/events/{event_id}")

    # ------------------------------------------------------------------
    # Workouts (library)
    # ------------------------------------------------------------------

    def get_workouts(self) -> list[dict]:
        """Fetch all workouts in the athlete's workout library."""
        return self._get(f"/api/v1/athlete/{self.athlete_id}/workouts")

    def get_workout(self, workout_id: str | int) -> dict:
        """Fetch a single workout's full definition."""
        return self._get(f"/api/v1/athlete/{self.athlete_id}/workouts/{workout_id}")

    def create_workout(self, data: dict) -> dict:
        """Create a new workout in the library.

        Args:
            data: Workout definition (name, type, description, moving_time, etc.).
        """
        return self._post(f"/api/v1/athlete/{self.athlete_id}/workouts", json=data)

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> Any:
        return self._request("GET", path, params=params)

    def _post(self, path: str, json: Any = None) -> Any:
        return self._request("POST", path, json=json)

    def _put(self, path: str, json: Any = None) -> Any:
        return self._request("PUT", path, json=json)

    def _delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{BASE_URL}{path}"
        kwargs.setdefault("timeout", self.timeout)
        try:
            response = self._session.request(method, url, **kwargs)
            response.raise_for_status()
        except requests.HTTPError as exc:
            body = exc.response.text[:500] if exc.response is not None else ""
            code = exc.response.status_code if exc.response is not None else None
            raise IntervalsAPIError(
                f"Intervals.icu API {method} {path} failed: HTTP {code} — {body}",
                status_code=code,
                response_body=body,
            ) from exc
        except requests.RequestException as exc:
            raise IntervalsAPIError(
                f"Intervals.icu API {method} {path} failed: {exc}"
            ) from exc

        if not response.content:
            return {}
        return response.json()
