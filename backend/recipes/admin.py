from django.contrib import admin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy
from shortener.admin import UrlMap, UrlProfile

from .models import (FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
                     ShoppingList, Tag, )


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline, )


admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(FavoriteRecipe)
admin.site.register(ShoppingList)

admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
admin.site.unregister(UrlMap)
admin.site.unregister(UrlProfile)
