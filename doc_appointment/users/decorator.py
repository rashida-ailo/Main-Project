from django.http import HttpResponseForbidden
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (
            request.user.is_superuser or request.user.role == 'admin'
        ):
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("Admins only")
    return _wrapped_view
