from rest_framework import permissions


class AuthorOrSafeMethodsOnly(permissions.BasePermission):
    def has_permission(self, request, *args):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, _, obj):
        return (request.user.is_authenticated and obj.author == request.user
                or request.method in permissions.SAFE_METHODS)
