from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm, CustomUserChangeForm

User = get_user_model()


class RegisterView(CreateView):
    """View for user registration"""
    model = User
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'  # Change this line
    success_url = reverse_lazy('recipes:recipe_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, f'Welcome {self.object.username}! Your account has been created.')
        return response


class ProfileView(LoginRequiredMixin, DetailView):
    """View for displaying user profile"""
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'user'
    
    def get_object(self):
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating user profile"""
    model = User
    form_class = CustomUserChangeForm
    template_name = 'accounts/profile_update.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Your profile has been updated successfully!')
        return response