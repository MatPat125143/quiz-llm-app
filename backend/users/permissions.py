from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and
                hasattr(request.user, 'profile') and
                request.user.profile.role == 'admin')

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.profile.role == 'admin':
            return True
        return obj.user == request.user