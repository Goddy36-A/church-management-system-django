"""
Member engagement scoring.

IMPORTANT: This score is an administrative participation indicator only.
It is derived from configurable, observable activity (attendance, ministry
and event participation, group membership) over a rolling window. It is
NOT a psychological, spiritual, or medical assessment of any individual,
and should always be presented to users with that context.
"""

from datetime import date, timedelta

from attendance.models import AttendanceRecord, AttendanceSession
from events.models import EventParticipant, Event

ENGAGEMENT_WINDOW_DAYS = 90

# Weights are configurable constants, explainable in the UI breakdown.
WEIGHTS = {
    "attendance": 0.45,
    "event_participation": 0.20,
    "ministry_participation": 0.15,
    "group_participation": 0.15,
    "recency": 0.05,
}

CATEGORY_THRESHOLDS = [
    (80, "Highly Engaged"),
    (60, "Engaged"),
    (40, "Moderately Engaged"),
    (20, "Low Engagement"),
    (0, "Inactive"),
]


def categorize(score: float) -> str:
    for threshold, label in CATEGORY_THRESHOLDS:
        if score >= threshold:
            return label
    return "Inactive"


def compute_member_engagement(member, window_days: int = ENGAGEMENT_WINDOW_DAYS) -> dict:
    since = date.today() - timedelta(days=window_days)

    total_sessions = AttendanceSession.objects.filter(session_date__gte=since).count()
    attended_sessions = AttendanceRecord.objects.filter(
        member_id=member.id, present=True, session__session_date__gte=since,
    ).count()
    attendance_rate = (attended_sessions / total_sessions * 100) if total_sessions else 0.0

    total_events = Event.objects.filter(start_date__gte=since, is_archived=False).count()
    attended_events = EventParticipant.objects.filter(
        member_id=member.id, attended=True, event__start_date__gte=since,
    ).count()
    event_rate = (attended_events / total_events * 100) if total_events else 0.0

    ministry_score = 100.0 if member.ministry_id else 0.0

    group_score = 100.0 if member.group_memberships.exists() else 0.0

    recent_attendance = AttendanceRecord.objects.filter(
        member_id=member.id, present=True,
        session__session_date__gte=date.today() - timedelta(days=30),
    ).count()
    recency_score = 100.0 if recent_attendance else 0.0

    composite = (
        attendance_rate * WEIGHTS["attendance"]
        + event_rate * WEIGHTS["event_participation"]
        + ministry_score * WEIGHTS["ministry_participation"]
        + group_score * WEIGHTS["group_participation"]
        + recency_score * WEIGHTS["recency"]
    )
    composite = round(min(composite, 100.0), 1)

    return {
        "score": composite,
        "category": categorize(composite),
        "breakdown": {
            "attendance_rate": round(attendance_rate, 1),
            "event_participation_rate": round(event_rate, 1),
            "ministry_participation": ministry_score,
            "group_participation": group_score,
            "recent_activity": recency_score,
        },
        "window_days": window_days,
    }


def bulk_engagement_summary(members, window_days: int = ENGAGEMENT_WINDOW_DAYS):
    """Compute engagement for a list of members and return summary stats + per-member scores."""
    results = []
    for m in members:
        data = compute_member_engagement(m, window_days)
        results.append({"member": m, **data})

    if not results:
        return {"members": [], "average_score": 0, "category_counts": {}}

    avg_score = round(sum(r["score"] for r in results) / len(results), 1)
    category_counts = {}
    for r in results:
        category_counts[r["category"]] = category_counts.get(r["category"], 0) + 1

    return {"members": results, "average_score": avg_score, "category_counts": category_counts}
