from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Subscribe

User = get_user_model()


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'first_name',
                    'last_name', 'is_active', 'recipes_count',
                    'subscribers_count', )
    search_fields = ('username', 'email', )

    @admin.display(description='Количество рецептов')
    def recipes_count(self, user):
        return user.recipes.count()

    @admin.display(description='Количество подписчиков')
    def subscribers_count(self, user):
        return user.following.count()


@admin.register(Subscribe)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'user')
    search_fields = ('subscriber__username', 'subscriber__email',
                     'user__username', 'user__email')
