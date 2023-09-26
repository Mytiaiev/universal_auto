from rest_framework import permissions


class IsPartnerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.groups.filter(name='Partner').exists()
        return False
