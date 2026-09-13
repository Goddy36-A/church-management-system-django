from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login


def roles_required(*role_names):
    """Restrict a view to users whose role is in role_names.
    Super admin is implicitly allowed everywhere for administrative continuity."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.has_role("super_admin") or request.user.has_role(*role_names):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapped
    return decorator


def finance_access_required(view_func):
    """Only roles allowed to see financial data."""

    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.can_view_finances():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapped
