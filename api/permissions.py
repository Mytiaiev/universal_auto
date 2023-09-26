from rest_framework import permissions


class IsPartnerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.groups.filter(name='Partner').exists()
        return False


class IsManagerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.groups.filter(name='Manager').exists()
        return False


class IsInvestorUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.groups.filter(name='Investor').exists()
        return False
