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
    measurement_unit = models.CharField(verbose_name='Мера измерения', max_length=32)

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')
    name = models.CharField(verbose_name='Название', max_length=64)
    image = models.ImageField()
    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient')
    image = models.ImageField(upload_to='recipes/', blank=False, null=False)
    text = models.TextField(max_length=256, blank=False, null=False)
    cooking_time = models.PositiveIntegerField(blank=False, null=False)

    def __str__(self) -> str:
        return self.name


class RecipeIngredient(models.Model):
    recipes = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipeingredient')
    ingredients = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(blank=False, null=False)

    def __str__(self) -> str:
        return f'{self.recipes.name} - {self.ingredients.name} - {self.amount}'


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='favorites')

    def __str__(self) -> str:
        return f'{self.user} - {self.recipe.name}'


class ShoppingList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False, 
                             related_name='shopping_user')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='shopping')

    def __str__(self) -> str:
        return f'{self.user} - {self.recipe.name}'