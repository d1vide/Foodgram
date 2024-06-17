import django_filters
from recipes.models import Ingredient, Recipe, Tag

class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='iregex')
    class Meta:
        model = Ingredient
        fields = {'name': ('startswith', )}



class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(method='get_is_in_shopping_cart')
    author = django_filters.NumberFilter(field_name='author__id')
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', )

    def get_is_favorited(self, queryset, _, value):
        pass

    def get_is_in_shopping_cart(self, queryset, _, value):
        pass
