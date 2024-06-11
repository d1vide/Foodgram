import base64, os
from djoser.views import UserViewSet as djoserUserViewSet
from rest_framework import filters, mixins, viewsets, permissions, pagination, status
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404


from .serializers import CustomUserSerializer, FavoriteResponseSerializer, FavoriteSerializer, RecipeUnsafeSerializer, IngredientSerializer, TagSerializer, RecipeSafeSerializer, SubscribeSerializer
from recipes.models import Recipe, Ingredient, Tag, FavoriteRecipe
from users.models import Subscribe


User = get_user_model()


class UserViewSet(djoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (permissions.AllowAny, )
    pagination_class = pagination.PageNumberPagination

    @action(methods=['PUT', 'DELETE'], detail=False, url_path='me/avatar')
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            try:
                format, imgstr = avatar_data.split(';base64,')
                ext = format.split('/')[-1]
                avatar = ContentFile(base64.b64decode(imgstr), name=f'image.{ext}')
            except TypeError:
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


    @action(methods=['POST', 'DELETE'], detail=True)
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
        if self.request.method in ['POST', 'PATCH', 'DEL']:
            return RecipeUnsafeSerializer
        return RecipeSafeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

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
        else:
            if not FavoriteRecipe.objects.filter(recipe=recipe, user=self.request.user).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            get_object_or_404(FavoriteRecipe, user=self.request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name',)


