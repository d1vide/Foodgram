from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(blank=False, null=False, unique=True)
    avatar = models.ImageField()
    is_subscribed = models.BooleanField(default=False)
