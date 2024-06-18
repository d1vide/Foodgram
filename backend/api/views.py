import base64, os
from shortener import shortener
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import filters, mixins, viewsets, permissions, pagination, status
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework.decorators import action
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.permissions import SAFE_METHODS
from rest_framework.generics import get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import (CustomUserSerializer, FavoriteAndShoppingCartResponseSerializer, FavoriteSerializer,
                            RecipeUnsafeSerializer, IngredientSerializer, TagSerializer,
                            RecipeSafeSerializer, SubscribeSerializer, ShoppingListSerializer, AvatarSerializer)
from recipes.models import Recipe, Ingredient, Tag, FavoriteRecipe, ShoppingList, RecipeIngredient
from .filters import IngredientFilter, RecipeFilter
from users.models import Subscribe
from .pagination import CustomPageNumberPagination
from .permissions import AuthorOrSafeMethodsOnly

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
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

    @action(['POST', 'DELETE'],
            detail=True)
    def subscribe(self, request, id):
        user = get_object_or_404(User, pk=id)
        subscriber = request.user
        if request.method == 'POST':
            serializer = SubscribeSerializer(user,
                                             data=request.data,
                                             context={'request': request})
            serializer.is_valid(raise_exception=True)
            if Subscribe.objects.filter(user=user, subscriber=subscriber).exists() or user == subscriber:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            Subscribe.objects.create(user=user, subscriber=subscriber)
            return Response(serializer.data,
                                     status=status.HTTP_201_CREATED)
        if not Subscribe.objects.filter(user=user, subscriber=subscriber).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(Subscribe, user=user, subscriber=subscriber).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, 
            permission_classes=(permissions.IsAuthenticated, ))
    def subscriptions(self, request):
        queryset = User.objects.filter(following__subscriber=request.user)
        serializer = SubscribeSerializer(self.paginate_queryset(queryset),
                                         many=True,
                                         context={'request': request})
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSafeSerializer
    permission_classes = (AuthorOrSafeMethodsOnly, )
    pagination_class = CustomPageNumberPagination
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSafeSerializer
        return RecipeUnsafeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _create_txt(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as file:
            for item in data:
                file.write(f'{item["ingredients__name"]}: {item["amount"]}{item["ingredients__measurement_unit"]} \n')

    @action(methods=['POST', 'DELETE'],
            detail=True)
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if FavoriteRecipe.objects.filter(recipe=recipe, user=self.request.user).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            data = {'recipe': recipe.pk, 'user': self.request.user.pk}
            serializer = FavoriteSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                response_serializer = FavoriteAndShoppingCartResponseSerializer(recipe)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        if not FavoriteRecipe.objects.filter(recipe=recipe, user=self.request.user).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(FavoriteRecipe, user=self.request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST', 'DELETE'], detail=True)
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if ShoppingList.objects.filter(recipe=recipe, user=self.request.user).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            data = {'recipe': recipe.pk, 'user': self.request.user.pk}
            serializer = ShoppingListSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                response_serializer = FavoriteAndShoppingCartResponseSerializer(recipe)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        if not ShoppingList.objects.filter(recipe=recipe, user=self.request.user).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(ShoppingList, user=self.request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET'], detail=False)
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(recipes__shopping__user=request.user).values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(amount=Sum('amount'))
        file = self._create_txt(ingredients, 'shopping_list.txt')
        return HttpResponse(file, content_type='text/plain')

    @action(methods=['GET'], detail=True, url_path='get-link')
    def get_short_link(self, request, pk):
        get_object_or_404(Recipe, pk=pk)
        original_url = request.build_absolute_uri(reverse('recipe-detail', args=(pk, )))
        user = request.user if request.user.is_authenticated else User.objects.get_or_create(username='guest')[0]
        short_link = shortener.create(user, original_url)
        return Response({'short-link': '/s/' + short_link})


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