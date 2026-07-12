from django.urls import path
from .views import (
    RecipeListView, RecipeDetailView, RecipeCreateView, 
    RecipeUpdateView, RecipeDeleteView, FavoriteToggleView,
    FavoritesListView, MyRecipesListView, MealPlanView,
    AddToMealPlanView, RemoveFromMealPlanView, nutrition_lookup_api, ingredient_search_api
)

app_name = 'recipes'

urlpatterns = [
    # Recipe URLs
    path('', RecipeListView.as_view(), name='recipe_list'),
    path('recipe/<int:pk>/', RecipeDetailView.as_view(), name='recipe_detail'),
    path('recipe/create/', RecipeCreateView.as_view(), name='recipe_create'),
    path('recipe/<int:pk>/update/', RecipeUpdateView.as_view(), name='recipe_update'),
    path('recipe/<int:pk>/delete/', RecipeDeleteView.as_view(), name='recipe_delete'),
    
    # Favorite URLs
    path('favorites/', FavoritesListView.as_view(), name='favorites'),
    path('favorite/<int:pk>/toggle/', FavoriteToggleView.as_view(), name='toggle_favorite'),
    
    # My Recipes
    path('my-recipes/', MyRecipesListView.as_view(), name='my_recipes'),
    
    # Meal Plan URLs
    path('meal-plan/', MealPlanView.as_view(), name='meal_plan'),
    path('meal-plan/add/', AddToMealPlanView.as_view(), name='add_to_meal_plan'),  # Changed - removed <int:pk>
    path('meal-plan/remove/', RemoveFromMealPlanView.as_view(), name='remove_from_meal_plan'),  # Changed - removed <int:pk>
    
    # API URLs
    path('api/nutrition/lookup/', nutrition_lookup_api, name='nutrition_lookup_api'),
    path('api/ingredients/search/', ingredient_search_api, name='ingredient_search_api'),
]