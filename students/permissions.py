from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def student_required(view_func):
    @login_required
    def _wrapped(request, *args, **kwargs):
        if getattr(request.user, "role", None) != "student":
            raise PermissionDenied("غير مصرح")
        return view_func(request, *args, **kwargs)
    return _wrapped
