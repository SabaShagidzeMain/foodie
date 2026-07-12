from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Recipe
from django.db import models


class RecipeOwnerRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user owns the recipe"""
    
    def test_func(self):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        return self.request.user == recipe.user or self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to do that.")
        return redirect('recipe_list')


class RecipeVisibilityMixin:
    """Mixin to handle recipe visibility logic"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            # Show public recipes + user's private recipes
            return queryset.filter(
                models.Q(is_public=True) | models.Q(user=self.request.user)
            )
        return queryset.filter(is_public=True)