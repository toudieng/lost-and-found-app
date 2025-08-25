from django.contrib import admin

from backend.objets.models import Declaration, Objet, Restitution

# Register your models here.
admin.site.register(Objet)
admin.site.register(Declaration)
admin.site.register(Restitution)