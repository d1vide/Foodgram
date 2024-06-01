from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(verbose_name='Название', max_length=64, unique=True)
    slug = models.SlugField(verbose_name='Идентификатор', max_length=64, unique=True)

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    name = models.CharField(verbose_name='Название', max_length=64)
    measurment_unit = models.CharField(verbose_name='Мера измерения', max_length=32)

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(verbose_name='Название', max_length=64)
    image = models.ImageField(blank=True, null=True)
    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient')
    is_favorited = models.BooleanField(default=False)
    is_in_shopping_cart = models.BooleanField(default=False)
    text = models.TextField(max_length=256, blank=True, null=True)
    cooking_time = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class RecipeIngredient(models.Model):
    recipes = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredients = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.recipes.name} - {self.ingredients.name}'


