from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Tag(models.Model):
    """Tags for categorizing recipes"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    
    # Common tag categories
    CATEGORY_CHOICES = [
        ('diet', 'Dietary'),
        ('cuisine', 'Cuisine'),
        ('meal_type', 'Meal Type'),
        ('difficulty', 'Difficulty'),
        ('time', 'Time'),
        ('special', 'Special'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='special')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

class Recipe(models.Model):
    """Main Recipe model"""
    
    CATEGORY_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('dessert', 'Dessert'),
        ('snack', 'Snack'),
        ('appetizer', 'Appetizer'),
        ('soup', 'Soup'),
        ('salad', 'Salad'),
        ('main_course', 'Main Course'),
        ('side_dish', 'Side Dish'),
        ('beverage', 'Beverage'),
    ]
    
    # Basic Info
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='main_course')
    
    # Time & Servings
    prep_time = models.PositiveIntegerField(help_text='Preparation time in minutes')
    cook_time = models.PositiveIntegerField(help_text='Cooking time in minutes')
    servings = models.PositiveIntegerField(default=4)
    
    # Additional Info
    image = models.ImageField(upload_to='recipe_images/', blank=True, null=True)
    is_public = models.BooleanField(default=True)
    
    # Ratings & Favorites
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_ratings = models.PositiveIntegerField(default=0)
    
    # Tags (Many-to-Many through RecipeTag)
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        related_name='recipes',
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    @property
    def total_time(self):
        """Calculate total time (prep + cook)"""
        return self.prep_time + self.cook_time
    
    @property
    def average_rating(self):
        """Calculate average rating if there are ratings"""
        return self.rating
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        indexes = [
            models.Index(fields=['user', 'is_public']),
            models.Index(fields=['category']),
            models.Index(fields=['created_at']),
        ]

class Ingredient(models.Model):
    """Ingredients for recipes"""
    
    UNIT_CHOICES = [
        ('g', 'Grams'),
        ('kg', 'Kilograms'),
        ('ml', 'Milliliters'),
        ('l', 'Liters'),
        ('tsp', 'Teaspoon'),
        ('tbsp', 'Tablespoon'),
        ('cup', 'Cup'),
        ('oz', 'Ounces'),
        ('lb', 'Pounds'),
        ('pinch', 'Pinch'),
        ('piece', 'Piece'),
        ('slice', 'Slice'),
        ('whole', 'Whole'),
    ]
    
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients'
    )
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='g')
    calories_per_100g = models.DecimalField(
    max_digits=10, 
    decimal_places=2, 
    default=0, 
    help_text='Calories per 100g'
)
    
    # Optional: Notes like "chopped", "melted", etc.
    notes = models.CharField(max_length=100, blank=True, default='')
    
    # For scaling
    is_optional = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.amount} {self.get_unit_display()} {self.name}"
    
    @property
    def total_calories(self):
        """Calculate total calories for this ingredient based on amount"""
        if self.calories_per_100g > 0:
            # Convert amount to grams based on unit
            amount_in_grams = self._convert_to_grams()
            return (self.calories_per_100g * amount_in_grams) / 100
        return 0
    
    def _convert_to_grams(self):
        """Helper to convert amount to grams for calorie calculation"""
        conversion = {
            'g': 1,
            'kg': 1000,
            'ml': 1,  # For water-like liquids
            'l': 1000,
            'tsp': 5,
            'tbsp': 15,
            'cup': 240,
            'oz': 28.35,
            'lb': 453.592,
        }
        return self.amount * conversion.get(self.unit, 1)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'

class RecipeTag(models.Model):
    """Through model for Recipe-Tag many-to-many relationship"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['recipe', 'tag']
        verbose_name = 'Recipe Tag'
        verbose_name_plural = 'Recipe Tags'

class Favorite(models.Model):
    """User's favorite recipes"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'recipe']
        ordering = ['-created_at']
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'