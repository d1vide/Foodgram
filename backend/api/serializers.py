from rest_framework import serializers, exceptions

from recipes.models import Recipe, RecipeIngredient, Ingredient, Tag, FavoriteRecipe, ShoppingList
from users.models import Subscribe
from django.db.models import F
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserSerializer(UserSerializer):
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
        return (cur_user
                and cur_user.is_authenticated
                and Subscribe.objects.filter(subscriber=cur_user,
                                             user=obj).exists())


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

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'name', 'text',
                  'cooking_time', 'image', )

    def to_representation(self, instance):
        serializer = RecipeSafeSerializer(instance, context=self.context)
        return serializer.data

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        recipeingredient_data = validated_data.pop('recipeingredient')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        for ingredient in recipeingredient_data:
            RecipeIngredient.objects.create(ingredients=ingredient.get('id'),
                                            recipes=recipe,
                                            amount=ingredient.get('amount'))
        return recipe

    def update(self, recipe, validated_data):
        tags_data = validated_data.pop('tags', None)
        recipeingredient_data = validated_data.pop('recipeingredient', None)   
        if tags_data is None:
            raise serializers.ValidationError({'tags': 'Поле tags обязательное'})
        if recipeingredient_data is None:
            raise serializers.ValidationError({'ingredients': 'Поле ingredients обязательное'})     
        if tags_data:
            recipe.tags.clear()
            recipe.tags.set(tags_data)
        if recipeingredient_data:
            recipe.ingredients.clear()
            for ing in recipeingredient_data:
                RecipeIngredient.objects.get_or_create(ingredients=ing.get('id'),
                                                       recipes=recipe,
                                                       amount=ing.get('amount'))
        return super().update(recipe, validated_data)

    def validate_ingredients(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise exceptions.ValidationError()
        check_repetitive_set = list()
        for ingredient in ingredients:
            if int(ingredient.get('amount')) <= 0:
                raise exceptions.ValidationError()
            if ingredient in check_repetitive_set:
                raise exceptions.ValidationError()
            check_repetitive_set.append(ingredient)
        return data

    def validate_tags(self, data):
        tags = self.initial_data.get('tags')
        if not tags:
            raise exceptions.ValidationError({'tags': 'Поле tags обязательное'})
        check_repetitive_set = set()
        for tag in tags:
            if tag in check_repetitive_set:
                raise exceptions.ValidationError({'tags': 'Поле tags должно быть уникальным'})
            check_repetitive_set.add(tag)
        return data

    def validate_cooking_time(self, data):
        cooking_time = self.initial_data.get('cooking_time')
        if cooking_time <= 0:
            raise exceptions.ValidationError({'cooking_time': 'Поле cooking_time должно быть положительным числом'})
        return data

    def validate_image(self, image):
        if not image:
            raise exceptions.ValidationError({'image': 'Поле image должно быть уникальным'})
        return image


class RecipeSafeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
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


class FavoriteAndShoppingCartResponseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time', )


class FavoriteSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = FavoriteRecipe
        fields = '__all__'


class SubscribeSerializer(serializers.ModelSerializer):
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
        serializer = FavoriteAndShoppingCartResponseSerializer(recipes,
                                                               many=True,
                                                               read_only=True)
        return serializer.data

    def get_is_subscribed(self, obj):
        cur_user = self.context.get('request').user
        return (cur_user
                and cur_user.is_authenticated
                and Subscribe.objects.filter(subscriber=cur_user,
                                             user=obj).exists())


class ShoppingListSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = ShoppingList
        fields = '__all__'


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar', )
