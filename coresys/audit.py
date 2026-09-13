from coresys.models import AuditLog


def log_action(request, action: str, entity_type: str = None, entity_id: int = None, description: str = None):
    """Record an audit trail entry. Never raises - a logging failure must not break the request."""
    try:
        user = getattr(request, "user", None)
        AuditLog.objects.create(
            user=user if user and user.is_authenticated else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
        )
    except Exception:
        pass
