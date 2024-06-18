from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint

from .constants import (INGREDIENT_NAME_LENGTH, INGREDIENT_UNIT_LENGTH,
                        RECIPE_NAME_LENGTH, RECIPE_TEXT_LENGTH,
                        TAG_NAME_LENGTH, TAG_SLUG_LENGTH, )


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(verbose_name='Название',
                            max_length=TAG_NAME_LENGTH,
                            unique=True)
    slug = models.SlugField(verbose_name='Идентификатор',
                            max_length=TAG_SLUG_LENGTH,
                            unique=True)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'
        ordering = ('name', 'slug', )

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    name = models.CharField(verbose_name='Название',
                            max_length=INGREDIENT_NAME_LENGTH)
    measurement_unit = models.CharField(verbose_name='Мера измерения',
                                        max_length=INGREDIENT_UNIT_LENGTH)

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name', )

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='recipes',
                               verbose_name='Автор')
    name = models.CharField(verbose_name='Название',
                            max_length=RECIPE_NAME_LENGTH)
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         verbose_name='Ингредиенты')
    image = models.ImageField(upload_to='recipes/',
                              blank=False, null=False,
                              verbose_name='Изображение')
    text = models.TextField(max_length=RECIPE_TEXT_LENGTH,
                            blank=False, null=False,
                            verbose_name='Описание')
    cooking_time = models.PositiveIntegerField(blank=False, null=False,
                                               verbose_name='Время готовки')

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('name', )

    def __str__(self) -> str:
        return self.name


class RecipeIngredient(models.Model):
    recipes = models.ForeignKey(Recipe,
                                on_delete=models.CASCADE,
                                related_name='recipeingredient',
                                verbose_name='Рецепт')
    ingredients = models.ForeignKey(Ingredient,
                                    on_delete=models.CASCADE,
                                    verbose_name='Ингредиент')
    amount = models.PositiveIntegerField(blank=False, null=False,
                                         verbose_name='Количество')

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self) -> str:
        return (f'У рецепта {self.recipes.name} '
                f'ингредиент {self.ingredients.name} в кол-ве {self.amount}')


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             blank=False, null=False,
                             verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='favorites',
                               verbose_name='Рецепт')

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранные'
        constraints = (UniqueConstraint(fields=['user', 'recipe'],
                                        name='unique_favorite'), )

    def __str__(self) -> str:
        return f'У пользователя {self.user} любимый рецепт {self.recipe.name}'


class ShoppingList(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             blank=False, null=False,
                             related_name='shopping_user',
                             verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='shopping',
                               verbose_name='Рецепт')

    class Meta:
        verbose_name = 'рецепт из списка'
        verbose_name_plural = 'Рецепты из списка'
        constraints = (UniqueConstraint(fields=['user', 'recipe'],
                                        name='unique_shopping_list'), )

    def __str__(self) -> str:
        return f'У пользователя {self.user} в списке рецепт {self.recipe.name}'
