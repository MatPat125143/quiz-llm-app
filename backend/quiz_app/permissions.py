from rest_framework import permissions


class IsQuizOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
            return True
        return obj.user == request.user
