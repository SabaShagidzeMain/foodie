from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import models
from .models import Recipe, Tag
from .forms import RecipeForm, IngredientFormSet
from .services import RecipeService, NutritionService, MealPlanService
from .mixins import RecipeOwnerRequiredMixin
import logging
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET

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
        
        context['ingredients'] = recipe.ingredients.all()
        
        scale_factor = int(self.request.GET.get('scale', 1))
        if scale_factor in [1, 2, 4]:
            context['scale_factor'] = scale_factor
            context['scaled'] = scale_factor > 1
        else:
            context['scale_factor'] = 1
            context['scaled'] = False
        
        nutrition_service = NutritionService()
        context['nutrition'] = nutrition_service.calculate_recipe_nutrition(recipe)
        
        return context


class RecipeCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new recipe with ingredients"""
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_form.html'
    success_url = reverse_lazy('recipes:recipe_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['ingredient_formset'] = IngredientFormSet(self.request.POST)
        else:
            context['ingredient_formset'] = IngredientFormSet()
        return context
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        context = self.get_context_data()
        ingredient_formset = context['ingredient_formset']
        
        if ingredient_formset.is_valid():
            self.object = form.save()
            ingredient_formset.instance = self.object
            ingredient_formset.save()
            messages.success(self.request, f'Recipe "{form.instance.title}" created successfully!')
            return super().form_valid(form)
        else:
            messages.error(self.request, "Please correct the errors below.")
            return self.render_to_response(self.get_context_data(form=form))


class RecipeUpdateView(LoginRequiredMixin, RecipeOwnerRequiredMixin, UpdateView):
    """View for updating a recipe with ingredients"""
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_form.html'
    success_url = reverse_lazy('recipes:recipe_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['ingredient_formset'] = IngredientFormSet(self.request.POST, instance=self.object)
        else:
            context['ingredient_formset'] = IngredientFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        ingredient_formset = context['ingredient_formset']
        
        if ingredient_formset.is_valid():
            self.object = form.save()
            ingredient_formset.instance = self.object
            ingredient_formset.save()
            messages.success(self.request, f'Recipe "{form.instance.title}" updated successfully!')
            return super().form_valid(form)
        else:
            messages.error(self.request, "Please correct the errors below.")
            return self.render_to_response(self.get_context_data(form=form))


class RecipeDeleteView(LoginRequiredMixin, RecipeOwnerRequiredMixin, DeleteView):
    """View for deleting a recipe"""
    model = Recipe
    template_name = 'recipes/recipe_confirm_delete.html'
    success_url = reverse_lazy('recipes:recipe_list')
    
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
        
        return redirect('recipes:recipe_detail', pk=recipe.id)


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
        week_start_str = self.request.GET.get('week_start')
        if week_start_str:
            try:
                week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            except ValueError:
                week_start = timezone.now().date()
        else:
            week_start = timezone.now().date()
        
        week_start = week_start - timedelta(days=week_start.weekday())
        return week_start
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        week_start = self._get_week_start()
        
        from apps.mealplans.models import MealPlan
        plans = MealPlan.objects.filter(
            user=self.request.user,
            week_start=week_start
        ).select_related('recipe')
        
        week_data = []
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day_num in range(7):
            day_info = {
                'day_num': day_num,
                'day_name': day_names[day_num],
                'breakfast': None,
                'lunch': None,
                'dinner': None,
                'snack': None
            }
            
            for plan in plans:
                if plan.day_of_week == day_num:
                    day_info[plan.meal_type] = plan.recipe
            
            week_data.append(day_info)
        
        context['week_data'] = week_data
        context['week_start'] = week_start
        context['week_end'] = week_start + timedelta(days=6)
        context['meal_types'] = ['breakfast', 'lunch', 'dinner', 'snack']
        
        service = MealPlanService(self.request.user)
        context['week_nutrition'] = service.get_week_nutrition(week_start)
        
        context['prev_week'] = week_start - timedelta(days=7)
        context['next_week'] = week_start + timedelta(days=7)
        
        return context


class AddToMealPlanView(LoginRequiredMixin, DetailView):
    """View for adding a recipe to the meal plan"""
    model = Recipe
    template_name = 'recipes/add_to_meal_plan.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
            return redirect('recipes:recipe_detail', pk=recipe.id)
        
        try:
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            day = int(day)
        except (ValueError, TypeError):
            messages.error(request, "Invalid date or day.")
            return redirect('recipes:recipe_detail', pk=recipe.id)
        
        service = MealPlanService(request.user)
        result = service.add_to_plan(week_start, day, meal_type, recipe.id)
        
        if result:
            messages.success(request, f'Added "{recipe.title}" to meal plan!')
        else:
            messages.error(request, "Could not add recipe to meal plan.")
        
        return redirect('recipes:meal_plan')


# ============ API Endpoints ============

@require_GET
def nutrition_lookup_api(request):
    """
    API endpoint to look up nutrition data for an ingredient.
    Used by the recipe form to auto-fill calories.
    """
    ingredient_name = request.GET.get('ingredient', '').strip()
    
    if not ingredient_name:
        return JsonResponse({
            'error': 'No ingredient provided'
        }, status=400)
    
    if len(ingredient_name) < 2:
        return JsonResponse({
            'error': 'Ingredient name must be at least 2 characters'
        }, status=400)
    
    try:
        service = NutritionService()
        nutrition_data = service.get_ingredient_nutrition(ingredient_name)
        
        if nutrition_data and nutrition_data.get('calories', 0) > 0:
            return JsonResponse({
                'success': True,
                'name': ingredient_name,
                'calories': nutrition_data.get('calories', 0),
                'protein': nutrition_data.get('protein', 0),
                'fat': nutrition_data.get('fat', 0),
                'carbs': nutrition_data.get('carbs', 0),
                'fiber': nutrition_data.get('fiber', 0),
                'message': f"Found {nutrition_data.get('calories', 0)} calories per 100g"
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Could not find nutrition data for this ingredient',
                'calories': 0
            }, status=404)
            
    except Exception as e:
        logger.error(f"Nutrition lookup error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while fetching nutrition data'
        }, status=500)


@require_GET
def ingredient_search_api(request):
    """
    API endpoint to search for ingredients from Edamam.
    Returns matching ingredients for autocomplete dropdown.
    """
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({
            'success': True,
            'results': []
        })
    
    try:
        service = NutritionService()
        results = service.search_ingredients(query)
        
        return JsonResponse({
            'success': True,
            'results': results
        })
    except Exception as e:
        logger.error(f"Ingredient search error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'results': []
        }, status=500)