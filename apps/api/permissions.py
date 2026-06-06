from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUser(BasePermission):
    """Только администраторы."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsManagerOrAdmin(BasePermission):
    """Менеджеры и администраторы."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('manager', 'admin')


class IsSupervisorOrAdmin(BasePermission):
    """Руководители и администраторы."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('supervisor', 'admin')


class IsOwnerOrAdmin(BasePermission):
    """Владелец объекта или администратор."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        manager = getattr(obj, 'manager', None)
        return manager == request.user


class ClientPermission(BasePermission):
    """
    GET  — любой авторизованный
    POST — менеджер / админ
    PUT/PATCH — менеджер (свой клиент) / админ
    DELETE — только админ
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        if request.method == 'DELETE':
            return request.user.is_admin
        return request.user.role in ('manager', 'admin')

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.method == 'DELETE':
            return request.user.is_admin
        if request.user.is_admin:
            return True
        return obj.manager == request.user


class RequestPermission(BasePermission):
    """
    GET  — любой авторизованный
    POST — менеджер / админ
    PATCH status — менеджер (своя заявка) / админ
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role in ('manager', 'admin')

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_admin:
            return True
        return obj.manager == request.user
