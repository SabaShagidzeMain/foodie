from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import models
from .models import Recipe, Tag
from .forms import RecipeForm
from .services import RecipeService, NutritionService, MealPlanService
from .mixins import RecipeOwnerRequiredMixin, RecipeVisibilityMixin
import logging
from django.http import JsonResponse
from django.core.paginator import Paginator

logger = logging.getLogger(__name__)


class RecipeListView(ListView):
    """View for listing recipes with search and filter"""
    model = Recipe
    template_name = 'recipes/recipe_list.html'
    context_object_name = 'recipes'
    paginate_by = 10
    
    def get_queryset(self):
        service = RecipeService(self.request.user if self.request.user.is_authenticated else None)
        search = self.request.GET.get('search')
        category = self.request.GET.get('category')
        tag = self.request.GET.get('tag')
        
        # Check if user wants to see their own recipes
        if self.request.GET.get('my_recipes') and self.request.user.is_authenticated:
            return Recipe.objects.filter(user=self.request.user).order_by('-created_at')
        
        return service.get_recipes(
            page=self.request.GET.get('page', 1),
            per_page=self.paginate_by,
            search=search,
            category=category,
            tag=tag,
            is_public=not self.request.GET.get('my_recipes')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['category'] = self.request.GET.get('category', '')
        context['tag_filter'] = self.request.GET.get('tag', '')
        context['categories'] = Recipe.CATEGORY_CHOICES
        context['tags'] = Tag.objects.all()
        return context


class RecipeDetailView(DetailView):
    """View for displaying a single recipe"""
    model = Recipe
    template_name = 'recipes/recipe_detail.html'
    context_object_name = 'recipe'
    
    def get_queryset(self):
        service = RecipeService(self.request.user if self.request.user.is_authenticated else None)
        recipe = service.get_recipe_detail(self.kwargs.get('pk'))
        if not recipe:
            return Recipe.objects.none()
        return Recipe.objects.filter(id=recipe.id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = context['recipe']
        
        # Get ingredients
        ingredients = recipe.ingredients.all()
        context['ingredients'] = ingredients
        
        # Handle serving scaling
        scale_factor = int(self.request.GET.get('scale', 1))
        if scale_factor in [1, 2, 4]:
            context['scale_factor'] = scale_factor
            context['scaled'] = scale_factor > 1
        else:
            context['scale_factor'] = 1
            context['scaled'] = False
        
        # Calculate nutrition
        nutrition_service = NutritionService()
        context['nutrition'] = nutrition_service.calculate_recipe_nutrition(recipe)
        
        return context


class RecipeCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new recipe"""
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_form.html'
    success_url = reverse_lazy('recipe_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Recipe "{form.instance.title}" created successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class RecipeUpdateView(LoginRequiredMixin, RecipeOwnerRequiredMixin, UpdateView):
    """View for updating a recipe"""
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_form.html'
    success_url = reverse_lazy('recipe_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Recipe "{form.instance.title}" updated successfully!')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class RecipeDeleteView(LoginRequiredMixin, RecipeOwnerRequiredMixin, DeleteView):
    """View for deleting a recipe"""
    model = Recipe
    template_name = 'recipes/recipe_confirm_delete.html'
    success_url = reverse_lazy('recipe_list')
    
    def delete(self, request, *args, **kwargs):
        recipe = self.get_object()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Recipe "{recipe.title}" deleted successfully!')
        return response


class FavoriteToggleView(LoginRequiredMixin, DetailView):
    """View for toggling favorite status"""
    model = Recipe
    
    def get(self, request, *args, **kwargs):
        recipe = self.get_object()
        service = RecipeService(request.user)
        is_favorited = service.toggle_favorite(recipe.id)
        
        if is_favorited:
            messages.success(request, f'Added "{recipe.title}" to favorites!')
        else:
            messages.info(request, f'Removed "{recipe.title}" from favorites.')
        
        return redirect('recipe_detail', pk=recipe.id)


class FavoritesListView(LoginRequiredMixin, ListView):
    """View for displaying user's favorite recipes"""
    model = Recipe
    template_name = 'recipes/favorites_list.html'
    context_object_name = 'recipes'
    paginate_by = 10
    
    def get_queryset(self):
        service = RecipeService(self.request.user)
        return service.get_favorites()


class MyRecipesListView(LoginRequiredMixin, ListView):
    """View for displaying user's own recipes"""
    model = Recipe
    template_name = 'recipes/my_recipes.html'
    context_object_name = 'recipes'
    paginate_by = 10
    
    def get_queryset(self):
        return Recipe.objects.filter(user=self.request.user).order_by('-created_at')


class MealPlanView(LoginRequiredMixin, ListView):
    """View for displaying the weekly meal plan"""
    model = Recipe
    template_name = 'mealplans/meal_plan.html'
    context_object_name = 'recipes'
    
    def _get_week_start(self):
        """Get the Monday of the current week"""
        week_start_str = self.request.GET.get('week_start')
        if week_start_str:
            try:
                week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            except ValueError:
                week_start = timezone.now().date()
        else:
            week_start = timezone.now().date()
        
        # Get Monday of the week
        week_start = week_start - timedelta(days=week_start.weekday())
        return week_start
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get week start
        week_start = self._get_week_start()
        
        # Get meal plans
        from apps.mealplans.models import MealPlan
        plans = MealPlan.objects.filter(
            user=self.request.user,
            week_start=week_start
        ).select_related('recipe')
        
        # Build a simple list for the template
        # Each item: {'day': 0, 'day_name': 'Monday', 'breakfast': recipe or None, 'lunch': ..., etc}
        week_data = []
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
        
        for day_num in range(7):
            day_info = {
                'day_num': day_num,
                'day_name': day_names[day_num],
                'breakfast': None,
                'lunch': None,
                'dinner': None,
                'snack': None
            }
            
            # Find plans for this day
            for plan in plans:
                if plan.day_of_week == day_num:
                    day_info[plan.meal_type] = plan.recipe
            
            week_data.append(day_info)
        
        context['week_data'] = week_data
        context['week_start'] = week_start
        context['week_end'] = week_start + timedelta(days=6)
        context['meal_types'] = ['breakfast', 'lunch', 'dinner', 'snack']
        
        # Get nutrition for the week
        service = MealPlanService(self.request.user)
        context['week_nutrition'] = service.get_week_nutrition(week_start)
        
        # Previous and next week
        context['prev_week'] = week_start - timedelta(days=7)
        context['next_week'] = week_start + timedelta(days=7)
        
        return context

class AddToMealPlanView(LoginRequiredMixin, DetailView):
    """View for adding a recipe to the meal plan"""
    model = Recipe
    template_name = 'recipes/add_to_meal_plan.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get week start
        week_start_str = self.request.GET.get('week_start')
        if week_start_str:
            try:
                week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            except ValueError:
                week_start = timezone.now().date()
        else:
            week_start = timezone.now().date()
        week_start = week_start - timedelta(days=week_start.weekday())
        
        context['week_start'] = week_start
        context['days'] = list(enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']))
        context['meal_types'] = ['breakfast', 'lunch', 'dinner', 'snack']
        return context
    
    def post(self, request, *args, **kwargs):
        recipe = self.get_object()
        week_start_str = request.POST.get('week_start')
        day = request.POST.get('day')
        meal_type = request.POST.get('meal_type')
        
        if not all([week_start_str, day, meal_type]):
            messages.error(request, "Missing required parameters.")
            return redirect('recipe_detail', pk=recipe.id)
        
        try:
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            day = int(day)
        except (ValueError, TypeError):
            messages.error(request, "Invalid date or day.")
            return redirect('recipe_detail', pk=recipe.id)
        
        service = MealPlanService(request.user)
        result = service.add_to_plan(week_start, day, meal_type, recipe.id)
        
        if result:
            messages.success(request, f'Added "{recipe.title}" to meal plan!')
        else:
            messages.error(request, "Could not add recipe to meal plan.")
        
        return redirect('meal_plan')