from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

def user_profile_image_path(instance, filename):
    return f'profile_images/{instance.id}/{filename}'

class User(AbstractUser):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    email = models.EmailField(unique=True)
    phone = models.CharField(validators=[phone_regex], max_length=17, unique=True)
    full_name = models.CharField(max_length=100)
    birth_date = models.DateField(null=True, blank=True)
    national_id = models.CharField(max_length=20, unique=True)
    profile_image = models.ImageField(
        upload_to=user_profile_image_path,
        null=True,
        blank=True
    )
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'phone', 'full_name', 'national_id']

    class Meta:
        db_table = 'auth_user'

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    privacy_settings = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"