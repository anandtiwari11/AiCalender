"""Deterministic calendar intelligence — AI explains; this module computes."""

from app.intelligence.chief_of_staff import build_chief_of_staff_brief
from app.intelligence.conflicts import detect_conflicts, resolve_conflict_alternatives
from app.intelligence.focus import focus_protection_plan
from app.intelligence.importance import score_meeting
from app.intelligence.buffers import buffer_recommendations
from app.intelligence.preferences import default_preferences, preferences_dict

__all__ = [
    "build_chief_of_staff_brief",
    "detect_conflicts",
    "resolve_conflict_alternatives",
    "focus_protection_plan",
    "score_meeting",
    "buffer_recommendations",
    "default_preferences",
    "preferences_dict",
]
