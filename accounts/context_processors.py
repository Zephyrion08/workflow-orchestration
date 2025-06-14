# accounts/context_processors.py

from .models import SignupRequest

def pending_requests_count(request):
    if request.user.is_authenticated and request.user.is_superuser:
        count = SignupRequest.objects.count()
        return {'pending_requests_count': count}
    return {'pending_requests_count': 0}
