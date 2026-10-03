import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from .services import answer_for_user, suggested_questions


@login_required
@require_GET
def status(request):
    return JsonResponse({"ready": True, "name": "Commercial-Grade AI Assistant", "role": getattr(request.user, "role", ""), "suggestions": suggested_questions(request.user)})


@login_required
@require_POST
def chat(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid request."}, status=400)
    message = str(payload.get("message", "")).strip()
    if not message:
        return JsonResponse({"error": "Please enter a question."}, status=400)
    if len(message) > 1000:
        return JsonResponse({"error": "Please keep your question below 1000 characters."}, status=400)
    result = answer_for_user(request.user, message)
    return JsonResponse({"reply": result["answer"], "answer_source": result["source"], "sources": result["sources"], "suggestions": suggested_questions(request.user)})
