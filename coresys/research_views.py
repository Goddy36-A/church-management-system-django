from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.models import RoleName

from .audit import log_action
from .decorators import roles_required
from .models import SurveyQuestion, SurveyResponse


@login_required
@roles_required(RoleName.ADMIN, RoleName.PASTOR)
def index(request):
    questions = SurveyQuestion.objects.filter(is_active=True).order_by("dimension", "display_order")

    results = []
    for q in questions:
        responses = list(q.responses.all())
        n = len(responses)
        mean = round(sum(r.score for r in responses) / n, 2) if n else 0
        counts = {i: sum(1 for r in responses if r.score == i) for i in range(1, 6)}
        percentages = {i: round(counts[i] / n * 100, 1) if n else 0 for i in range(1, 6)}
        demo_count = sum(1 for r in responses if r.is_demo_data)
        results.append({
            "question": q, "n": n, "mean": mean, "counts": counts,
            "percentages": percentages, "demo_count": demo_count,
        })

    return render(request, "research/index.html", {"results": results})


@login_required
@roles_required(RoleName.ADMIN)
def add_question(request):
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        dimension = request.POST.get("dimension", "administrative_efficiency")
        if not text:
            messages.error(request, "Question text is required.")
            return redirect("research:add_question")
        q = SurveyQuestion.objects.create(text=text, dimension=dimension)
        log_action(request, "survey_question.create", entity_type="SurveyQuestion", entity_id=q.id)
        messages.success(request, "Evaluation question added.")
        return redirect("research:index")

    return render(request, "research/question_form.html")


@login_required
def respond(request):
    """Any logged-in user (staff or member) can submit their evaluation responses."""
    questions = SurveyQuestion.objects.filter(is_active=True).order_by("dimension", "display_order")

    if request.method == "POST":
        for q in questions:
            score_raw = request.POST.get(f"question_{q.id}")
            score = int(score_raw) if score_raw and score_raw.isdigit() else None
            if score and 1 <= score <= 5:
                SurveyResponse.objects.create(
                    question=q,
                    respondent=request.user,
                    respondent_role=request.user.role.name if request.user.role else None,
                    score=score,
                    is_demo_data=False,
                )
        log_action(request, "survey_response.submit", description="Submitted evaluation survey")
        messages.success(request, "Thank you - your evaluation responses have been recorded.")
        return redirect("dashboard:index")

    return render(request, "research/respond.html", {"questions": questions})
