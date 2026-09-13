from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from coresys.audit import log_action
from coresys.decorators import finance_access_required
from members.models import Member

from .models import Contribution, ContributionCategory


@login_required
@finance_access_required
def index(request):
    category_id = request.GET.get("category_id", "")
    start = request.GET.get("start", "")
    end = request.GET.get("end", "")

    query = Contribution.objects.all()
    if category_id:
        query = query.filter(category_id=category_id)
    if start:
        try:
            query = query.filter(contribution_date__gte=datetime.strptime(start, "%Y-%m-%d").date())
        except ValueError:
            pass
    if end:
        try:
            query = query.filter(contribution_date__lte=datetime.strptime(end, "%Y-%m-%d").date())
        except ValueError:
            pass

    contributions = query.order_by("-contribution_date")
    total = sum(float(c.amount) for c in contributions)
    categories = ContributionCategory.objects.filter(is_active=True).order_by("name")

    return render(request, "contributions/index.html", {
        "contributions": contributions, "total": total, "categories": categories,
        "category_id": category_id, "start": start, "end": end,
    })


@login_required
@finance_access_required
def create(request):
    members = Member.objects.filter(is_archived=False).order_by("last_name")
    categories = ContributionCategory.objects.filter(is_active=True).order_by("name")

    if request.method == "POST":
        try:
            amount = Decimal(request.POST.get("amount", "0"))
        except InvalidOperation:
            messages.error(request, "Enter a valid amount.")
            return redirect("contributions:create")

        if amount <= 0:
            messages.error(request, "Amount must be greater than zero.")
            return redirect("contributions:create")

        category_id = request.POST.get("category_id")
        if not category_id:
            messages.error(request, "Please select a category.")
            return redirect("contributions:create")

        date_raw = request.POST.get("contribution_date")
        try:
            c_date = datetime.strptime(date_raw, "%Y-%m-%d").date() if date_raw else date.today()
        except ValueError:
            c_date = date.today()

        c = Contribution.objects.create(
            member_id=request.POST.get("member_id") or None,
            category_id=category_id,
            amount=amount,
            contribution_date=c_date,
            payment_method=request.POST.get("payment_method", "cash"),
            reference=request.POST.get("reference", "").strip() or None,
            notes=request.POST.get("notes", "").strip() or None,
            recorded_by=request.user,
        )
        log_action(request, "contribution.create", entity_type="Contribution", entity_id=c.id,
                   description=f"Recorded {c.amount} {c.currency}")
        messages.success(request, "Contribution recorded.")
        return redirect("contributions:index")

    return render(request, "contributions/form.html", {"members": members, "categories": categories})


@login_required
@finance_access_required
def categories(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            ContributionCategory.objects.create(name=name, description=request.POST.get("description", "").strip() or None)
            log_action(request, "contribution_category.create", description=name)
            messages.success(request, f"Category '{name}' created.")
        return redirect("contributions:categories")

    cats = ContributionCategory.objects.order_by("name")
    return render(request, "contributions/categories.html", {"categories": cats})


@login_required
@finance_access_required
def reports(request):
    since = date.today() - timedelta(days=365)
    contributions = Contribution.objects.filter(contribution_date__gte=since)

    by_category = {}
    by_month = {}
    for c in contributions:
        cat_name = c.category.name if c.category else "Uncategorized"
        by_category[cat_name] = by_category.get(cat_name, 0) + float(c.amount)
        month_key = c.contribution_date.strftime("%Y-%m")
        by_month[month_key] = by_month.get(month_key, 0) + float(c.amount)

    sorted_months = sorted(by_month.keys())

    return render(request, "contributions/reports.html", {
        "by_category": by_category,
        "month_labels": sorted_months,
        "month_values": [by_month[m] for m in sorted_months],
        "total": sum(float(c.amount) for c in contributions),
    })
