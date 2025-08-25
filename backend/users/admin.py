from django.contrib import admin

from backend.users.models import Commissariat, Utilisateur

# Register your models here.
admin.site.register(Utilisateur)
admin.site.register(Commissariat)