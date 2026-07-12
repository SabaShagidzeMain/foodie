from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class MealPlan(models.Model):
    """Weekly meal planning model"""
    
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='meal_plans'
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name='meal_plans'
    )
    week_start = models.DateField(help_text='Start date of the week (Monday)')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    
    # Optional notes
    notes = models.TextField(blank=True, default='')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_day_of_week_display()} - {self.get_meal_type_display()}: {self.recipe.title}"
    
    class Meta:
        ordering = ['week_start', 'day_of_week', 'meal_type']
        unique_together = ['user', 'week_start', 'day_of_week', 'meal_type']
        verbose_name = 'Meal Plan'
        verbose_name_plural = 'Meal Plans'
        indexes = [
            models.Index(fields=['user', 'week_start']),
            models.Index(fields=['day_of_week']),
        ]