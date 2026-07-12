from django.urls import path
from .views import (
    RecipeListView, RecipeDetailView, RecipeCreateView, 
    RecipeUpdateView, RecipeDeleteView, FavoriteToggleView,
    FavoritesListView, MyRecipesListView, MealPlanView,
    AddToMealPlanView
)

app_name = 'recipes'

urlpatterns = [
    path('', RecipeListView.as_view(), name='recipe_list'),  # This must exist
    path('recipe/<int:pk>/', RecipeDetailView.as_view(), name='recipe_detail'),
    path('recipe/create/', RecipeCreateView.as_view(), name='recipe_create'),
    path('recipe/<int:pk>/update/', RecipeUpdateView.as_view(), name='recipe_update'),
    path('recipe/<int:pk>/delete/', RecipeDeleteView.as_view(), name='recipe_delete'),
    path('favorites/', FavoritesListView.as_view(), name='favorites'),
    path('favorite/<int:pk>/toggle/', FavoriteToggleView.as_view(), name='toggle_favorite'),
    path('my-recipes/', MyRecipesListView.as_view(), name='my_recipes'),
    path('meal-plan/', MealPlanView.as_view(), name='meal_plan'),
    path('meal-plan/add/<int:pk>/', AddToMealPlanView.as_view(), name='add_to_meal_plan'),
]