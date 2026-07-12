from django.contrib import admin
from django.utils.html import format_html
from .models import Recipe, Ingredient, Tag, RecipeTag, Favorite

class IngredientInline(admin.TabularInline):
    """Inline editing for ingredients"""
    model = Ingredient
    extra = 1
    fields = ['name', 'amount', 'unit', 'calories_per_100g', 'notes', 'is_optional']

class RecipeTagInline(admin.TabularInline):
    """Inline editing for tags"""
    model = RecipeTag
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'servings', 'is_public', 'rating', 'created_at']
    list_filter = ['is_public', 'category', 'tags', 'created_at']
    search_fields = ['title', 'description', 'user__username']
    readonly_fields = ['rating', 'total_ratings', 'created_at', 'updated_at']
    
    inlines = [IngredientInline, RecipeTagInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description', 'category', 'image')
        }),
        ('Time & Servings', {
            'fields': ('prep_time', 'cook_time', 'servings')
        }),
        ('Visibility & Ratings', {
            'fields': ('is_public', 'rating', 'total_ratings')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'recipe', 'amount', 'unit', 'calories_per_100g']
    list_filter = ['unit', 'is_optional']
    search_fields = ['name', 'recipe__title']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipe')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category']
    list_filter = ['category']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipe', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'recipe__title']
    readonly_fields = ['created_at']