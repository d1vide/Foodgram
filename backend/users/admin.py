from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Subscribe

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'last_login', 'first_name',
                    'last_name', 'is_active', 'date_joined', 'avatar', )
    search_fields = ('username', 'email', )


@admin.register(Subscribe)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'user')
    search_fields = ('subscriber__username', 'subscriber__email',
                     'user__username', 'user__email')
