from django.contrib import admin

from backend.users.models import Message

# Register your models here.

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'date_envoi', 'traite')
    list_filter = ('traite', 'date_envoi')
    search_fields = ('nom', 'email', 'contenu')
