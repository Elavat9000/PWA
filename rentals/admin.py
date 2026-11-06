from django.contrib import admin

from .models import RentalRequest


@admin.register(RentalRequest)
class RentalRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'vehicle', 'start_date', 'end_date', 'days', 'total_cost', 'status')
    list_filter = ('status',)
    search_fields = ('user__username', 'vehicle__brand', 'vehicle__model')
    list_select_related = ('user', 'vehicle')
    readonly_fields = ('user', 'vehicle', 'start_date', 'end_date', 'days',
                       'daily_price', 'total_cost', 'created_at')
    fields = (*readonly_fields, 'status')
    actions = None

    @admin.display(description='días')
    def days(self, obj):
        return obj.days

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
