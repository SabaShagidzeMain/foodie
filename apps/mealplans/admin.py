from django.contrib import admin
from .models import MealPlan

@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipe', 'week_start', 'day_of_week', 'meal_type']
    list_filter = ['week_start', 'day_of_week', 'meal_type']
    search_fields = ['user__username', 'recipe__title']
    date_hierarchy = 'week_start'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'recipe')