import django_filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name', )


class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.NumberFilter(method='get_is_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='get_is_in_shopping_cart')
    author = django_filters.NumberFilter(field_name='author__id')
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    tags = django_filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                                    queryset=Tag.objects.all(),
                                                    to_field_name='slug')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', )

    def get_is_favorited(self, queryset, _, value):
        user = self.request.user
        if value == 1 and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, _, value):
        user = self.request.user
        if value == 1 and user.is_authenticated:
            return queryset.filter(shopping__user=user)
        return queryset
