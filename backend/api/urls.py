from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import RecipeViewSet, IngredientViewSet, TagViewSet, UserViewSet

router_v1 = DefaultRouter()

router_v1.register(r'tags', TagViewSet)
router_v1.register(r'ingredients', IngredientViewSet)
router_v1.register(r'recipes', RecipeViewSet)
router_v1.register(r'users', UserViewSet)

urlpatterns = [
    # path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    # path('recipes/<int:pk>/favorite/', add_delete_favorite),
    path('', include(router_v1.urls)),
]
