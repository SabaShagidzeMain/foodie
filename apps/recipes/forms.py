from django import forms
from django.forms import inlineformset_factory
from .models import Recipe, Ingredient


class RecipeForm(forms.ModelForm):
    """Form for creating and updating recipes"""
    
    class Meta:
        model = Recipe
        fields = [
            'title', 'description', 'category', 'prep_time', 
            'cook_time', 'servings', 'is_public'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'prep_time': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'cook_time': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'servings': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'prep_time': 'Prep Time (minutes)',
            'cook_time': 'Cook Time (minutes)',
            'is_public': 'Make this recipe public',
        }
        help_texts = {
            'prep_time': 'Time needed to prepare ingredients',
            'cook_time': 'Time needed to cook',
            'servings': 'Number of servings this recipe makes',
        }
    
    def clean_title(self):
        """Validate that title is not empty and unique for the user"""
        title = self.cleaned_data.get('title')
        if not title or len(title.strip()) < 3:
            raise forms.ValidationError("Title must be at least 3 characters long.")
        
        # Check for duplicate titles (excluding current instance)
        user = self.instance.user if self.instance.pk else None
        if user:
            existing = Recipe.objects.filter(user=user, title__iexact=title)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError("You already have a recipe with this title.")
        
        return title.strip()
    
    def clean_prep_time(self):
        """Validate prep time is positive"""
        prep_time = self.cleaned_data.get('prep_time')
        if prep_time is not None and prep_time < 0:
            raise forms.ValidationError("Prep time cannot be negative.")
        if prep_time is not None and prep_time > 1440:  # 24 hours
            raise forms.ValidationError("Prep time cannot exceed 24 hours (1440 minutes).")
        return prep_time
    
    def clean_cook_time(self):
        """Validate cook time is positive"""
        cook_time = self.cleaned_data.get('cook_time')
        if cook_time is not None and cook_time < 0:
            raise forms.ValidationError("Cook time cannot be negative.")
        if cook_time is not None and cook_time > 1440:  # 24 hours
            raise forms.ValidationError("Cook time cannot exceed 24 hours (1440 minutes).")
        return cook_time
    
    def clean_servings(self):
        """Validate servings is at least 1"""
        servings = self.cleaned_data.get('servings')
        if servings is not None and servings < 1:
            raise forms.ValidationError("Servings must be at least 1.")
        if servings is not None and servings > 100:
            raise forms.ValidationError("Servings cannot exceed 100.")
        return servings


class IngredientForm(forms.ModelForm):
    """Form for ingredients (used in inline formset)"""
    
    class Meta:
        model = Ingredient
        fields = ['name', 'amount', 'unit', 'calories_per_100g', 'notes', 'is_optional']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Flour'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'calories_per_100g': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., chopped, melted'}),
            'is_optional': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'calories_per_100g': 'Calories per 100g',
            'is_optional': 'Optional ingredient',
        }
        help_texts = {
            'calories_per_100g': 'Leave 0 if unknown (will try to fetch from API)',
        }
    
    def clean_amount(self):
        """Validate amount is positive"""
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0.")
        return amount
    
    def clean_name(self):
        """Validate ingredient name"""
        name = self.cleaned_data.get('name')
        if not name or len(name.strip()) < 2:
            raise forms.ValidationError("Ingredient name must be at least 2 characters long.")
        return name.strip()


# Create an inline formset for ingredients
IngredientFormSet = inlineformset_factory(
    Recipe,
    Ingredient,
    form=IngredientForm,
    extra=3,
    min_num=1,
    max_num=20,
    validate_min=True,
    can_delete=True
)