from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication


class TrackingJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user = result[0]
            type(user).objects.filter(pk=user.pk).update(last_seen_at=timezone.now())
        return result
