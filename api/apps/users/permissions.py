from django.utils.translation import gettext_lazy as _
from rest_framework import permissions
from api.apps.users.models import Role


class IsBuyer(permissions.IsAuthenticated):
    """
    Allows access only to buyers.
    """

    message = _("You don't have buyer permissions for this operation.")
    code = "is_not_buyer"

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == Role.BUYER
    

class IsSeller(permissions.IsAuthenticated):
    """
    Allows access only to sellers.
    """

    message = _("You don't have seller permissions for this operation.")
    code = "is_not_seller"

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == Role.SELLER


class IsProductOwner(IsSeller):
    """
    Allows access only to the product owner.
    """
    
    message = "You can only modify products you created."
    code = "is_not_product_owner"
    
    def has_object_permission(self, request, view, obj):
        return super().has_permission(request, view) and obj.seller == request.user


class IsProductOwnerOrReadOnly(IsProductOwner):
    """
    Allows access only to product owners or read only.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return super().has_permission(request, view)
