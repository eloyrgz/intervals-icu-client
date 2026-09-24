"""Shared Intervals.icu API client for training-coach-agent and plan-generator."""

from intervals_icu_client.client import IntervalsClient
from intervals_icu_client.exceptions import IntervalsAPIError

__all__ = ["IntervalsClient", "IntervalsAPIError"]
__version__ = "0.1.1"
