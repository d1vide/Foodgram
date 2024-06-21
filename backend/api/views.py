import os

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import Http404, FileResponse
from django.urls import reverse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import SAFE_METHODS
from shortener import shortener

from .constants import NOT_EXIST_ERROR, REPEAT_ERROR
from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPageNumberPagination
from .permissions import AuthorOrSafeMethodsOnly
from .serializers import (AvatarSerializer, UserSerializer,
                          FavoriteSerializer,
                          FavoriteShoppingResponseSerializer,
                          IngredientSerializer, RecipeSafeSerializer,
                          RecipeUnsafeSerializer, TagSerializer,
                          SubscribeSerializer, SubscribeResponseSerializer,
                          ShoppingListSerializer, )
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingList, Tag)
from users.models import Subscribe

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )
    pagination_class = CustomPageNumberPagination

    @action(["GET"],
            detail=False,
            permission_classes=(permissions.IsAuthenticated, ))
    def me(self, *args, **kwargs):
        return super().me(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        data.pop('avatar', None)
        data.pop('is_subscribed', None)
        return Response(data, status=status.HTTP_201_CREATED)

    @action(['PUT', 'DELETE'],
            detail=False,
            url_path='me/avatar',
            permission_classes=(permissions.IsAuthenticated, ))
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user.avatar = serializer.validated_data['avatar']
            user.save()
            avatar_url = request.build_absolute_uri(user.avatar.url)
            return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)
        try:
            os.remove(user.avatar.path)
        finally:
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['POST'],
            detail=True)
    def subscribe(self, request, id):
        user = get_object_or_404(User, pk=id)
        subscriber = request.user
        data = {'subscriber': subscriber.pk, 'user': user.pk}
        serializer = SubscribeSerializer(data=data)
        serializer_response = SubscribeResponseSerializer(
            user,
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer_response.data,
                        status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        user = get_object_or_404(User, pk=id)
        subscriber = request.user
        try:
            get_object_or_404(Subscribe, user=user,
                              subscriber=subscriber).delete()
        except Http404:
            return Response(REPEAT_ERROR,
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            permission_classes=(permissions.IsAuthenticated, ))
    def subscriptions(self, request):
        queryset = User.objects.filter(following__subscriber=request.user)
        serializer = SubscribeResponseSerializer(
            self.paginate_queryset(queryset), many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().select_related(
        'author').prefetch_related(
            'tags', 'ingredients', 'recipeingredient__ingredients')
    permission_classes = (AuthorOrSafeMethodsOnly, )
    pagination_class = CustomPageNumberPagination
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSafeSerializer
        return RecipeUnsafeSerializer

    def _create_txt(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as file:
            for item in data:
                file.write(f'{item["ingredients__name"]}: '
                           f'{item["amount"]}'
                           f'{item["ingredients__measurement_unit"]} \n')

    @staticmethod
    def _favorite_shopping_list_post(request, model, recipe_pk,
                                     serializerclass):
        recipe = get_object_or_404(Recipe, pk=recipe_pk)
        user = request.user
        if model.objects.filter(recipe=recipe, user=user).exists():
            return Response(REPEAT_ERROR, status=status.HTTP_400_BAD_REQUEST)
        data = {'recipe': recipe.pk, 'user': user.id}
        serializer = serializerclass(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer_response = FavoriteShoppingResponseSerializer(recipe)
        return Response(serializer_response.data,
                        status=status.HTTP_201_CREATED)

    @staticmethod
    def _favorite_shopping_list_delete(request, model, recipe_pk):
        recipe = get_object_or_404(Recipe, pk=recipe_pk)
        user = request.user.id
        try:
            get_object_or_404(model, recipe=recipe, user=user).delete()
        except Http404:
            return Response(NOT_EXIST_ERROR,
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST'],
            detail=True)
    def favorite(self, request, pk=None):
        return self._favorite_shopping_list_post(request,
                                                 FavoriteRecipe,
                                                 pk,
                                                 FavoriteSerializer)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self._favorite_shopping_list_delete(request, FavoriteRecipe, pk)

    @action(methods=['POST'], detail=True)
    def shopping_cart(self, request, pk=None):
        return self._favorite_shopping_list_post(request,
                                                 ShoppingList,
                                                 pk,
                                                 ShoppingListSerializer)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self._favorite_shopping_list_delete(request, ShoppingList, pk)

    @action(methods=['GET'], detail=False,
            permission_classes=(permissions.IsAuthenticated, ))
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipes__shopping__user=request.user).values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(amount=Sum('amount'))
        self._create_txt(ingredients, 'shopping_list.txt')
        return FileResponse(open('shopping_list.txt', "rb"),
                            as_attachment=True,
                            filename="shopping_List.txt",
                            content_type='text/plain')

    @action(methods=['GET'], detail=True, url_path='get-link')
    def get_short_link(self, request, pk):
        original_url = request.build_absolute_uri(reverse('recipe-detail',
                                                          args=(pk, )))
        original_url = original_url.replace('api/', '')
        user = (request.user if request.user.is_authenticated
                else User.objects.get_or_create(username='guest')[0])
        short_link = shortener.create(user, original_url)
        link = request.build_absolute_uri(f'/s/{short_link}')
        return Response({'short-link': link})


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter

