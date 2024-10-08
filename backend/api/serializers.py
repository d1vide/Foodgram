from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db.models import F
from djoser.serializers import UserSerializer as DjoserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, exceptions

from foodgram_backend.constants import (IMAGE_REQUIERED_ERROR,
                                        INGREDIENT_REPEAT_ERROR,
                                        INGREDIENT_REQUIERED_ERROR,
                                        REPEAT_ERROR,
                                        TAG_REPEAT_ERROR, TAG_REQUIERED_ERROR,
                                        SELF_SUBSCRIBE_ERROR)
from recipes.models import (FavoriteRecipe, Recipe, RecipeIngredient,
                            Ingredient, Tag, ShoppingList)
from users.models import Subscribe

User = get_user_model()


def is_subscribed(user, obj):
    return (user
            and user.is_authenticated
            and Subscribe.objects.filter(subscriber=user,
                                         user=obj).exists())


class UserSerializer(DjoserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password', 'is_subscribed', 'avatar')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'], )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def get_is_subscribed(self, obj):
        cur_user = self.context.get('request').user
        return is_subscribed(cur_user, obj)


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
    name = serializers.CharField(source='ingredients.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredients.measurement_unit',
        read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount', 'name', 'measurement_unit', )


class RecipeUnsafeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipeingredient')
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(
        validators=[MinValueValidator(1)])

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'name', 'text',
                  'cooking_time', 'image', )

    @staticmethod
    def _create_ingredients(recipeingredient, recipe):
        ingredients = []
        for ingr in recipeingredient:
            ingredient = RecipeIngredient(ingredients=ingr['id'],
                                          recipes=recipe,
                                          amount=ingr['amount'])
            ingredients.append(ingredient)
        RecipeIngredient.objects.bulk_create(ingredients)

    def to_representation(self, instance):
        serializer = RecipeSafeSerializer(instance, context=self.context)
        return serializer.data

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', None)
        recipeingredient_data = validated_data.pop('recipeingredient', None)
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self._create_ingredients(recipeingredient_data, recipe)
        return recipe

    def update(self, recipe, validated_data):
        tags_data = validated_data.pop('tags', None)
        recipeingredient_data = validated_data.pop('recipeingredient', None)
        recipe.tags.clear()
        recipe.tags.set(tags_data)
        recipe.ingredients.clear()
        self._create_ingredients(recipeingredient_data, recipe)
        return super().update(recipe, validated_data)

    def validate(self, attrs):
        if 'tags' not in attrs:
            raise serializers.ValidationError(TAG_REQUIERED_ERROR)
        if 'recipeingredient' not in attrs:
            raise serializers.ValidationError(INGREDIENT_REQUIERED_ERROR)
        return attrs

    def validate_ingredients(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise exceptions.ValidationError(INGREDIENT_REQUIERED_ERROR)
        for ingredient in ingredients:
            serializer = RecipeIngredientSerializer(data=ingredient)
            serializer.is_valid(raise_exception=True)
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise exceptions.ValidationError(INGREDIENT_REPEAT_ERROR)
        return data

    def validate_tags(self, data):
        tags = self.initial_data.get('tags')
        if not tags:
            raise exceptions.ValidationError(TAG_REQUIERED_ERROR)
        tag_ids = [tag for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise exceptions.ValidationError(TAG_REPEAT_ERROR)
        return data

    def validate_image(self, image):
        if not image:
            raise exceptions.ValidationError(IMAGE_REQUIERED_ERROR)
        return image


class RecipeSafeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField(allow_null=False)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time', )

    def get_ingredients(self, obj):
        recipe = obj
        ingredients = recipe.ingredients.annotate(
            amount=F('recipeingredient__amount')).values(
            'id', 'name', 'amount', 'measurement_unit',)
        return ingredients

    def get_is_favorited(self, obj):
        cur_user = self.context.get('request').user
        return (cur_user
                and cur_user.is_authenticated
                and FavoriteRecipe.objects.filter(recipe=obj,
                                                  user=cur_user).exists())

    def get_is_in_shopping_cart(self, obj):
        cur_user = self.context.get('request').user
        return (cur_user
                and cur_user.is_authenticated
                and ShoppingList.objects.filter(recipe=obj,
                                                user=cur_user).exists())


class FavoriteShoppingResponseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time', )


class RecipeUserBaseSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        abstract = True


class FavoriteSerializer(RecipeUserBaseSerializer):

    class Meta:
        model = FavoriteRecipe
        fields = '__all__'


class ShoppingListSerializer(RecipeUserBaseSerializer):

    class Meta:
        model = ShoppingList
        fields = '__all__'


class SubscribeResponseSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar', )
        read_only_fields = ('email', 'username', 'last_name',
                            'first_name', 'avatar')

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        recipes_limit = self.context.get('request').GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = FavoriteShoppingResponseSerializer(recipes,
                                                        many=True,
                                                        read_only=True)
        return serializer.data

    def get_is_subscribed(self, obj):
        cur_user = self.context.get('request').user
        return is_subscribed(cur_user, obj)


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = ('subscriber', 'user', )

    def validate(self, attrs):
        subscriber = attrs['subscriber']
        user = attrs['user']
        if subscriber == user:
            raise exceptions.ValidationError(SELF_SUBSCRIBE_ERROR)
        if Subscribe.objects.filter(user=user,
                                    subscriber=subscriber).exists():
            raise exceptions.ValidationError(REPEAT_ERROR)
        return super().validate(attrs)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar', )
