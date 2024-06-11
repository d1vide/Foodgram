from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    first_name = models.CharField(max_length=128, blank=False, null=False)
    last_name = models.CharField(max_length=128, blank=False, null=False)
    email = models.EmailField(blank=False, null=False, unique=True)
    avatar = models.ImageField(upload_to='users/')
    is_subscribed = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


class Subscribe(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriber') # тот кто подписан
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following') # тот на кого подписан

