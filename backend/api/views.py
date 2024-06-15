import base64, os
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

from .serializers import (CustomUserSerializer, FavoriteResponseSerializer, FavoriteSerializer,
                            RecipeUnsafeSerializer, IngredientSerializer, TagSerializer,
                            RecipeSafeSerializer, SubscribeSerializer, ShoppingListSerializer)
from recipes.models import Recipe, Ingredient, Tag, FavoriteRecipe, ShoppingList, RecipeIngredient
from users.models import Subscribe
from .pagination import CustomPageNumberPagination

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )
    pagination_class = CustomPageNumberPagination

    @action(["GET"], detail=False, permission_classes=(permissions.IsAuthenticated, ))
    def me(self, *args, **kwargs):
        return super().me(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        data = response.data
        data.pop('avatar')
        data.pop('is_subscribed')
        return Response(data, status=status.HTTP_201_CREATED)

    @action(['PUT', 'DELETE'], detail=False, url_path='me/avatar', permission_classes=(permissions.IsAuthenticated, ))
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            try:
                format, imgstr = avatar_data.split(';base64,')
                ext = format.split('/')[-1]
                avatar = ContentFile(base64.b64decode(imgstr), name=f'image.{ext}')
            except Exception:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            user.avatar = avatar
            user.save()

            avatar_url = request.build_absolute_uri(user.avatar.url)
            return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)
        try:
            os.remove(user.avatar.path)
        finally:
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(['POST', 'DELETE'], detail=True)
    def subscribe(self, request, id):
        user = get_object_or_404(User, pk=id)
        subscriber = request.user
        if request.method == 'POST':
            serializer = SubscribeSerializer(user,
                                             data=request.data,
                                             context={'request': request})
            serializer.is_valid(raise_exception=True)
            Subscribe.objects.create(user=user, subscriber=subscriber)
            return Response(serializer.data,
                                     status=status.HTTP_201_CREATED)
        if not Subscribe.objects.filter(user=user, subscriber=subscriber).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(Subscribe, user=user, subscriber=subscriber).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False)
    def subscriptions(self, request):
        queryset = User.objects.filter(following__subscriber=request.user)
        serializer = SubscribeSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data,
                        status=status.HTTP_200_OK)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSafeSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )
    pagination_class = pagination.PageNumberPagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSafeSerializer
        return RecipeUnsafeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _create_txt(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as file:
            for item in data:
                file.write(f'{item["ingredients__name"]}: {item["amount"]}{item["ingredients__measurment_unit"]} \n')


    @action(methods=['POST', 'DELETE'], detail=True)
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if FavoriteRecipe.objects.filter(recipe=recipe, user=self.request.user).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            data = {'recipe': recipe.pk, 'user': self.request.user.pk}
            serializer = FavoriteSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                response_serializer = FavoriteResponseSerializer(recipe)
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
                response_serializer = FavoriteResponseSerializer(recipe)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        if not ShoppingList.objects.filter(recipe=recipe, user=self.request.user).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(ShoppingList, user=self.request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET'], detail=False)
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(recipes__shopping__user=request.user).values(
            'ingredients__name',
            'ingredients__measurment_unit'
        ).annotate(amount=Sum('amount'))
        file = self._create_txt(ingredients, 'shopping_list.txt')
        return HttpResponse(file, content_type='text/plain')

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name',)


