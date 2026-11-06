from django.contrib import admin

from .models import KnowledgeEntry


@admin.register(KnowledgeEntry)
class KnowledgeEntryAdmin(admin.ModelAdmin):
    list_display = ('question', 'status', 'asked_by', 'updated_at')
    list_filter = ('status',)
    search_fields = ('question', 'answer')
    readonly_fields = ('asked_by', 'created_at', 'updated_at')
    fields = ('question', 'answer', 'status', *readonly_fields)
    actions = None
