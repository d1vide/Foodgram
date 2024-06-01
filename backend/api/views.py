from djoser.views import UserViewSet as djoserUserViewSet
from rest_framework import filters, mixins, viewsets
from django.contrib.auth import get_user_model

from .serializers import CustomUserSerializer, IngredientSerializer, TagSerializer
from recipes.models import Ingredient, Tag


User = get_user_model()

class UserViewSet(djoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name',)


