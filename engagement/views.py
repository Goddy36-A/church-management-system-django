from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.models import RoleName
from coresys.decorators import roles_required
from members.models import Member, Ministry

from .services import bulk_engagement_summary

VIEW_ROLES = (RoleName.ADMIN, RoleName.PASTOR, RoleName.MINISTRY_LEADER)


@login_required
@roles_required(*VIEW_ROLES)
def index(request):
    members = list(Member.objects.filter(is_archived=False))
    summary = bulk_engagement_summary(members)

    ministries = Ministry.objects.filter(is_archived=False)
    ministry_scores = []
    for ministry in ministries:
        ministry_members = [m for m in members if m.ministry_id == ministry.id]
        if not ministry_members:
            continue
        m_summary = bulk_engagement_summary(ministry_members)
        ministry_scores.append({
            "ministry": ministry.name, "average_score": m_summary["average_score"],
            "member_count": len(ministry_members),
        })

    needs_followup = sorted(
        [r for r in summary["members"] if r["score"] < 40], key=lambda r: r["score"]
    )[:20]

    return render(request, "engagement/index.html", {
        "summary": summary, "ministry_scores": ministry_scores, "needs_followup": needs_followup,
    })
