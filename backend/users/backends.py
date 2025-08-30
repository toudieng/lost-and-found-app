from django.contrib.auth.backends import ModelBackend
from .models import Utilisateur

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None
