from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import RoleName
from coresys.audit import log_action
from coresys.decorators import roles_required
from members.models import Ministry

from .models import Event, EventParticipant, EventStatus

EDITOR_ROLES = (RoleName.ADMIN, RoleName.PASTOR, RoleName.MINISTRY_LEADER)


@login_required
def index(request):
    show_past = request.GET.get("past") == "1"
    query = Event.objects.filter(is_archived=False)
    if show_past:
        query = query.filter(start_date__lt=date.today())
    else:
        query = query.filter(start_date__gte=date.today())
    events_list = query.order_by("start_date")
    can_manage = request.user.has_role(*EDITOR_ROLES, RoleName.SUPER_ADMIN)
    return render(request, "events/index.html", {"events": events_list, "show_past": show_past, "can_manage": can_manage})


@login_required
@roles_required(*EDITOR_ROLES)
def create(request):
    ministries = Ministry.objects.filter(is_archived=False).order_by("name")
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        start_date_raw = request.POST.get("start_date")
        if not title or not start_date_raw:
            messages.error(request, "Title and start date are required.")
            return redirect("events:create")
        try:
            start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid start date.")
            return redirect("events:create")

        end_date_raw = request.POST.get("end_date")
        end_date = None
        if end_date_raw:
            try:
                end_date = datetime.strptime(end_date_raw, "%Y-%m-%d").date()
            except ValueError:
                pass

        max_participants_raw = request.POST.get("max_participants")
        max_participants = int(max_participants_raw) if max_participants_raw and max_participants_raw.isdigit() else None

        event = Event.objects.create(
            title=title,
            description=request.POST.get("description", "").strip() or None,
            event_type=request.POST.get("event_type", "").strip() or None,
            start_date=start_date,
            end_date=end_date,
            location=request.POST.get("location", "").strip() or None,
            organizer=request.user,
            ministry_id=request.POST.get("ministry_id") or None,
            max_participants=max_participants,
            status=request.POST.get("status", EventStatus.PLANNED),
        )
        log_action(request, "event.create", entity_type="Event", entity_id=event.id, description=f"Created event {event.title}")
        messages.success(request, f"Event '{event.title}' created.")
        return redirect("events:view", event_id=event.id)

    return render(request, "events/form.html", {"ministries": ministries, "statuses": EventStatus.ALL})


@login_required
def view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    can_manage = request.user.has_role(*EDITOR_ROLES, RoleName.SUPER_ADMIN)
    already_registered = False
    if request.user.member_id:
        already_registered = event.participants.filter(member_id=request.user.member_id).exists()
    return render(request, "events/view.html", {
        "event": event, "can_manage": can_manage, "already_registered": already_registered,
    })


@login_required
def register(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    member_id = request.user.member_id or request.POST.get("member_id")
    if not member_id:
        messages.warning(request, "No member profile linked to this account.")
        return redirect("events:view", event_id=event_id)

    if event.max_participants and event.registered_count >= event.max_participants:
        messages.warning(request, "This event has reached its maximum number of participants.")
        return redirect("events:view", event_id=event_id)

    if not EventParticipant.objects.filter(event_id=event.id, member_id=member_id).exists():
        EventParticipant.objects.create(event_id=event.id, member_id=member_id)
        log_action(request, "event.register", entity_type="Event", entity_id=event.id)
        messages.success(request, "Registered for the event.")
    return redirect("events:view", event_id=event_id)


@login_required
@roles_required(*EDITOR_ROLES)
def attendance(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        attended_ids = {int(x) for x in request.POST.getlist("attended_member_ids") if x.isdigit()}
        for p in event.participants.all():
            p.attended = p.member_id in attended_ids
            p.save()
        log_action(request, "event.attendance", entity_type="Event", entity_id=event.id)
        messages.success(request, "Event attendance recorded.")
        return redirect("events:view", event_id=event_id)
    return render(request, "events/attendance.html", {"event": event})


@login_required
@roles_required(*EDITOR_ROLES)
def archive(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.is_archived = True
    event.save()
    log_action(request, "event.archive", entity_type="Event", entity_id=event.id)
    messages.info(request, "Event archived.")
    return redirect("events:index")
