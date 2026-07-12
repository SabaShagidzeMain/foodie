from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom User model with dietary preferences"""
    
    DIETARY_CHOICES = [
        ('none', 'No Restrictions'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('gluten_free', 'Gluten-Free'),
        ('keto', 'Keto'),
        ('paleo', 'Paleo'),
        ('dairy_free', 'Dairy-Free'),
        ('nut_free', 'Nut-Free'),
    ]
    
    dietary_pref = models.CharField(
        max_length=20,
        choices=DIETARY_CHOICES,
        default='none',
        verbose_name='Dietary Preference'
    )
    
    # Optional: Add a profile picture
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True
    )
    
    # Optional: Bio
    bio = models.TextField(
        max_length=500,
        blank=True,
        default=''
    )
    
    def __str__(self):
        return self.username
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'