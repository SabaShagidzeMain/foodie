from django.db import transaction
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from .models import Recipe, Ingredient, Tag, Favorite
import requests
import logging
from decouple import config

logger = logging.getLogger(__name__)
User = get_user_model()


class RecipeService:
    """Service class for handling recipe operations"""
    
    def __init__(self, user=None):
        self.user = user
    
    def get_recipes(self, page=1, per_page=10, search=None, category=None, tag=None, is_public=True):
        """Get recipes with filtering and pagination"""
        queryset = Recipe.objects.select_related('user').prefetch_related('tags', 'ingredients')
        
        # Filter by visibility
        if is_public:
            queryset = queryset.filter(is_public=True)
        
        # If user is authenticated, include their private recipes
        if self.user and self.user.is_authenticated:
            queryset = queryset.filter(Q(is_public=True) | Q(user=self.user))
        
        # Search
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(ingredients__name__icontains=search)
            ).distinct()
        
        # Filter by category
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by tag
        if tag:
            queryset = queryset.filter(tags__slug=tag)
        
        # Order by newest first
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        paginator = Paginator(queryset, per_page)
        return paginator.get_page(page)
    
    def get_recipe_detail(self, recipe_id):
        """Get a single recipe with all related data"""
        try:
            recipe = Recipe.objects.select_related('user').prefetch_related(
                'tags', 'ingredients', 'favorited_by'
            ).get(id=recipe_id)
            
            # Check if user can view this recipe
            if not recipe.is_public and (not self.user or recipe.user != self.user):
                return None
            
            return recipe
        except Recipe.DoesNotExist:
            return None
    
    @transaction.atomic
    def create_recipe(self, data):
        """Create a new recipe with ingredients and tags"""
        # Create recipe
        recipe = Recipe.objects.create(
            user=self.user,
            title=data.get('title'),
            description=data.get('description'),
            prep_time=data.get('prep_time'),
            cook_time=data.get('cook_time'),
            servings=data.get('servings', 4),
            category=data.get('category', 'main_course'),
            is_public=data.get('is_public', True)
        )
        
        # Add ingredients
        ingredients_data = data.get('ingredients', [])
        for ing_data in ingredients_data:
            Ingredient.objects.create(
                recipe=recipe,
                name=ing_data.get('name'),
                amount=ing_data.get('amount'),
                unit=ing_data.get('unit', 'g'),
                calories_per_100g=ing_data.get('calories_per_100g', 0),
                notes=ing_data.get('notes', ''),
                is_optional=ing_data.get('is_optional', False)
            )
        
        # Add tags
        tag_slugs = data.get('tags', [])
        for slug in tag_slugs:
            try:
                tag = Tag.objects.get(slug=slug)
                recipe.tags.add(tag)
            except Tag.DoesNotExist:
                pass
        
        return recipe
    
    @transaction.atomic
    def update_recipe(self, recipe_id, data):
        """Update an existing recipe"""
        recipe = self.get_recipe_detail(recipe_id)
        
        if not recipe or (recipe.user != self.user and not self.user.is_superuser):
            return None
        
        # Update basic fields
        for field in ['title', 'description', 'prep_time', 'cook_time', 
                      'servings', 'category', 'is_public']:
            if field in data:
                setattr(recipe, field, data[field])
        recipe.save()
        
        # Update ingredients (delete and recreate)
        if 'ingredients' in data:
            recipe.ingredients.all().delete()
            for ing_data in data['ingredients']:
                Ingredient.objects.create(
                    recipe=recipe,
                    name=ing_data.get('name'),
                    amount=ing_data.get('amount'),
                    unit=ing_data.get('unit', 'g'),
                    calories_per_100g=ing_data.get('calories_per_100g', 0),
                    notes=ing_data.get('notes', ''),
                    is_optional=ing_data.get('is_optional', False)
                )
        
        # Update tags
        if 'tags' in data:
            recipe.tags.clear()
            for slug in data['tags']:
                try:
                    tag = Tag.objects.get(slug=slug)
                    recipe.tags.add(tag)
                except Tag.DoesNotExist:
                    pass
        
        return recipe
    
    def delete_recipe(self, recipe_id):
        """Delete a recipe"""
        recipe = self.get_recipe_detail(recipe_id)
        if recipe and (recipe.user == self.user or self.user.is_superuser):
            recipe.delete()
            return True
        return False
    
    def scale_servings(self, recipe_id, factor):
        """Scale recipe ingredients for different serving sizes"""
        recipe = self.get_recipe_detail(recipe_id)
        if not recipe:
            return None
        
        # Create a scaled copy
        scaled_data = {
            'title': f"{recipe.title} (×{factor})",
            'description': recipe.description,
            'prep_time': recipe.prep_time,
            'cook_time': recipe.cook_time,
            'servings': recipe.servings * factor,
            'category': recipe.category,
            'is_public': False,  # Scaled versions are private by default
            'ingredients': []
        }
        
        # Scale ingredients
        for ingredient in recipe.ingredients.all():
            scaled_data['ingredients'].append({
                'name': ingredient.name,
                'amount': ingredient.amount * factor,
                'unit': ingredient.unit,
                'calories_per_100g': ingredient.calories_per_100g,
                'notes': ingredient.notes,
                'is_optional': ingredient.is_optional
            })
        
        # Add tags
        scaled_data['tags'] = list(recipe.tags.values_list('slug', flat=True))
        
        return self.create_recipe(scaled_data)
    
    def toggle_favorite(self, recipe_id):
        """Toggle favorite status for a recipe"""
        recipe = self.get_recipe_detail(recipe_id)
        if not recipe:
            return None
        
        favorite, created = Favorite.objects.get_or_create(
            user=self.user,
            recipe=recipe
        )
        
        if not created:
            favorite.delete()
            return False  # Unfavorited
        
        return True  # Favorited
    
    def get_favorites(self):
        """Get user's favorite recipes"""
        if not self.user or not self.user.is_authenticated:
            return []
        return Recipe.objects.filter(favorited_by__user=self.user)
    
    def rate_recipe(self, recipe_id, rating):
        """Rate a recipe"""
        recipe = self.get_recipe_detail(recipe_id)
        if not recipe:
            return None
        
        # Simple rating system - just update average
        # In a real app, you'd have a separate Rating model
        current_total = recipe.rating * recipe.total_ratings
        recipe.total_ratings += 1
        recipe.rating = (current_total + rating) / recipe.total_ratings
        recipe.save()
        
        return recipe.rating


class NutritionService:
    """Service for handling nutrition-related operations"""
    
    def __init__(self):
        self.app_id = config('EDAMAM_APP_ID', default='')
        self.app_key = config('EDAMAM_APP_KEY', default='')
    
    def get_ingredient_nutrition(self, ingredient_name):
        """Fetch nutrition data from Edamam API"""
        if not self.app_id or not self.app_key:
            logger.warning("Edamam API credentials not configured")
            return None
        
        url = "https://api.edamam.com/api/nutrition-data"
        params = {
            'app_id': self.app_id,
            'app_key': self.app_key,
            'ingr': ingredient_name
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Initialize nutrition values
            calories = 0
            protein = 0
            fat = 0
            carbs = 0
            fiber = 0
            
            # The nutrition data is inside ingredients[0].parsed[0].nutrients
            if 'ingredients' in data and len(data['ingredients']) > 0:
                ingredient_data = data['ingredients'][0]
                
                # Check if parsed data exists
                if 'parsed' in ingredient_data and len(ingredient_data['parsed']) > 0:
                    parsed_data = ingredient_data['parsed'][0]
                    
                    # Check if nutrients are available
                    if 'nutrients' in parsed_data:
                        nutrients = parsed_data['nutrients']
                        
                        # Extract calories (ENERC_KCAL)
                        if 'ENERC_KCAL' in nutrients:
                            calories = nutrients['ENERC_KCAL'].get('quantity', 0)
                        
                        # Extract protein (PROCNT)
                        if 'PROCNT' in nutrients:
                            protein = nutrients['PROCNT'].get('quantity', 0)
                        
                        # Extract fat (FAT)
                        if 'FAT' in nutrients:
                            fat = nutrients['FAT'].get('quantity', 0)
                        
                        # Extract carbs (CHOCDF)
                        if 'CHOCDF' in nutrients:
                            carbs = nutrients['CHOCDF'].get('quantity', 0)
                        
                        # Extract fiber (FIBTG)
                        if 'FIBTG' in nutrients:
                            fiber = nutrients['FIBTG'].get('quantity', 0)
            
            # If no data found in parsed, try the totalNutrients fallback
            if calories == 0 and 'totalNutrients' in data:
                nutrients = data['totalNutrients']
                calories = nutrients.get('ENERC_KCAL', {}).get('quantity', 0)
                protein = nutrients.get('PROCNT', {}).get('quantity', 0)
                fat = nutrients.get('FAT', {}).get('quantity', 0)
                carbs = nutrients.get('CHOCDF', {}).get('quantity', 0)
                fiber = nutrients.get('FIBTG', {}).get('quantity', 0)
            
            # If still no calories, try direct calories field
            if calories == 0 and 'calories' in data:
                calories = data.get('calories', 0)
            
            return {
                'name': ingredient_name,
                'calories': round(calories, 1),
                'protein': round(protein, 1),
                'fat': round(fat, 1),
                'carbs': round(carbs, 1),
                'fiber': round(fiber, 1),
            }
        except requests.RequestException as e:
            logger.error(f"Error fetching nutrition data: {e}")
            return None
    
    def calculate_recipe_nutrition(self, recipe):
        """Calculate total nutrition for a recipe"""
        total_calories = 0
        total_protein = 0
        total_fat = 0
        total_carbs = 0
        total_fiber = 0
        
        for ingredient in recipe.ingredients.all():
            # Use stored calories if available
            if ingredient.calories_per_100g > 0:
                # Convert to grams and calculate
                amount_in_grams = self._convert_to_grams(ingredient)
                calories = (ingredient.calories_per_100g * amount_in_grams) / 100
                total_calories += calories
            else:
                # Try to fetch from API
                nutrition = self.get_ingredient_nutrition(ingredient.name)
                if nutrition and nutrition.get('calories', 0) > 0:
                    amount_in_grams = self._convert_to_grams(ingredient)
                    # The API returns nutrition for the full ingredient amount
                    # So we need to scale it based on our amount
                    # First, get the weight from the API response
                    weight = self._get_ingredient_weight(ingredient.name)
                    if weight > 0:
                        # Scale calories based on weight
                        calories_per_gram = nutrition.get('calories', 0) / weight
                        calories = calories_per_gram * amount_in_grams
                    else:
                        # Fallback: use per 100g
                        calories_per_100g = nutrition.get('calories', 0)
                        calories = (calories_per_100g * amount_in_grams) / 100
                    
                    total_calories += calories
                    
                    # Add other nutrients
                    if weight > 0:
                        protein_per_gram = nutrition.get('protein', 0) / weight
                        fat_per_gram = nutrition.get('fat', 0) / weight
                        carbs_per_gram = nutrition.get('carbs', 0) / weight
                        fiber_per_gram = nutrition.get('fiber', 0) / weight
                        
                        total_protein += protein_per_gram * amount_in_grams
                        total_fat += fat_per_gram * amount_in_grams
                        total_carbs += carbs_per_gram * amount_in_grams
                        total_fiber += fiber_per_gram * amount_in_grams
        
        return {
            'calories': round(total_calories, 2),
            'protein': round(total_protein, 2),
            'fat': round(total_fat, 2),
            'carbs': round(total_carbs, 2),
            'fiber': round(total_fiber, 2),
            'per_serving': {
                'calories': round(total_calories / recipe.servings, 2),
                'protein': round(total_protein / recipe.servings, 2),
                'fat': round(total_fat / recipe.servings, 2),
                'carbs': round(total_carbs / recipe.servings, 2),
                'fiber': round(total_fiber / recipe.servings, 2),
            }
        }
    
    def _convert_to_grams(self, ingredient):
        """Convert ingredient amount to grams"""
        conversion = {
            'g': 1,
            'kg': 1000,
            'ml': 1,
            'l': 1000,
            'tsp': 5,
            'tbsp': 15,
            'cup': 240,
            'oz': 28.35,
            'lb': 453.592,
            'whole': 150,  # Approximate
            'piece': 100,  # Approximate
            'slice': 50,   # Approximate
            'pinch': 1,    # Approximate
        }
        return float(ingredient.amount) * conversion.get(ingredient.unit, 1)
    
    def _get_ingredient_weight(self, ingredient_name):
        """Get the weight of an ingredient from the API"""
        if not self.app_id or not self.app_key:
            return 0
        
        url = "https://api.edamam.com/api/nutrition-data"
        params = {
            'app_id': self.app_id,
            'app_key': self.app_key,
            'ingr': ingredient_name
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'ingredients' in data and len(data['ingredients']) > 0:
                ingredient_data = data['ingredients'][0]
                if 'parsed' in ingredient_data and len(ingredient_data['parsed']) > 0:
                    return ingredient_data['parsed'][0].get('weight', 0)
            return 0
        except:
            return 0


class MealPlanService:
    """Service for handling meal planning operations"""
    
    def __init__(self, user):
        self.user = user
    
    def get_weekly_plan(self, week_start):
        """Get the weekly meal plan for a user"""
        from apps.mealplans.models import MealPlan
        
        plans = MealPlan.objects.filter(
            user=self.user,
            week_start=week_start
        ).select_related('recipe')
        
        # Organize by day and meal type
        weekly_plan = {day: {meal: None for meal in ['breakfast', 'lunch', 'dinner', 'snack']} 
                      for day in range(7)}
        
        for plan in plans:
            weekly_plan[plan.day_of_week][plan.meal_type] = plan.recipe
        
        return weekly_plan
    
    def add_to_plan(self, week_start, day_of_week, meal_type, recipe_id):
        """Add a recipe to the meal plan"""
        from apps.mealplans.models import MealPlan
        from apps.recipes.models import Recipe
        
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            
            # Check if user can access this recipe
            if not recipe.is_public and recipe.user != self.user:
                return None
            
            # Create or update meal plan entry
            plan, created = MealPlan.objects.update_or_create(
                user=self.user,
                week_start=week_start,
                day_of_week=day_of_week,
                meal_type=meal_type,
                defaults={'recipe': recipe}
            )
            return plan
        except Recipe.DoesNotExist:
            return None
    
    def remove_from_plan(self, week_start, day_of_week, meal_type):
        """Remove a meal from the plan"""
        from apps.mealplans.models import MealPlan
        
        MealPlan.objects.filter(
            user=self.user,
            week_start=week_start,
            day_of_week=day_of_week,
            meal_type=meal_type
        ).delete()
        return True
    
    def get_week_nutrition(self, week_start):
        """Calculate nutrition for the entire week"""
        from apps.mealplans.models import MealPlan
        
        plans = MealPlan.objects.filter(
            user=self.user,
            week_start=week_start
        ).select_related('recipe')
        
        nutrition_service = NutritionService()
        total_calories = 0
        meal_count = 0
        
        for plan in plans:
            nutrition = nutrition_service.calculate_recipe_nutrition(plan.recipe)
            total_calories += nutrition.get('calories', 0)
            meal_count += 1
        
        return {
            'total_calories': round(total_calories, 2),
            'total_meals': meal_count,
            'average_calories': round(total_calories / meal_count, 2) if meal_count > 0 else 0,
            'daily_average': round(total_calories / 7, 2) if meal_count > 0 else 0,
        }