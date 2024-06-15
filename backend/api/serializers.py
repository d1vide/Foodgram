from rest_framework import serializers

from recipes.models import Recipe, RecipeIngredient, Ingredient, Tag, FavoriteRecipe, ShoppingList
from users.models import Subscribe

from djoser.serializers import UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'password', 'is_subscribed', 'avatar')
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def get_is_subscribed(self, obj):
        cur_user = self.context.get('request').user
        if not cur_user.is_authenticated:
            return False
        return Subscribe.objects.filter(subscriber=cur_user, user=obj).exists()


    # def create(self, validated_data):
    #     password = validated_data.pop('password', None)
    #     instance = self.Meta.model(**validated_data)
    #     instance.is_active = True
    #     if password is not None:  
    #         instance.set_password(password)
    #     instance.save()
    #     return instance

    # def to_representation(self, instance):
    #     return {
    #             "email": instance.email,
    #             "username": instance.username,
    #             "first_name": instance.first_name,
    #             "last_name": instance.last_name,
    #             "password": instance.password
    #         }


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'

class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount', )

class RecipeUnsafeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientSerializer(many=True, source='recipeingredient_set')

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'name', 'text', 'cooking_time', )

    def create(self, validated_data):
        tag_data = validated_data.pop('tags')
        recipeingredient = validated_data.pop('recipeingredient_set')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tag_data)
        for ingredient in recipeingredient:
            RecipeIngredient.objects.create(ingredients=ingredient.get('id'),
                                            recipes=recipe,
                                            amount=ingredient.get('amount'))
        return recipe

class RecipeSafeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True, source='recipeingredient_set')
    is_favorited = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_is_favorited(self, obj):
        cur_user = self.context.get('request').user
        return FavoriteRecipe.objects.filter(recipe=obj, user=cur_user).exists()

class RecipeOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', )


class FavoriteResponseSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=True)
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', )

class FavoriteSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model = FavoriteRecipe
        fields = '__all__'


class SubscribeSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 
                  'password', 'recipes', 'recipes_count', )
        read_only_fields = ('email', 'username', 'last_name', 'first_name', 'password')
    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        recipes_limit = self.context.get('request').GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = RecipeOutputSerializer(recipes, many=True, read_only=True)
        return serializer.data


class ShoppingListSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model = ShoppingList
        fields = '__all__'