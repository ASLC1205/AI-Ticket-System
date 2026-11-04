"""Role-based permissions for the AI SupportHub API.

JWT authentication identifies the user; these permissions authorize that
authenticated user using the role stored in the database.
"""
from rest_framework.permissions import BasePermission

def _authenticated_user(request):
    user = getattr(request, "user", None)
    return user if user and user.is_authenticated else None

def _is_admin(user):
    """An application admin must also have Django staff privileges."""
    return bool(user and user.is_authenticated
                and getattr(user, "role", None) == "ADMIN"
                and (user.is_staff or user.is_superuser))

class IsAuthenticatedRole(BasePermission):
    """Base permission for endpoints restricted to one application role."""
    role = None
    message = "You do not have permission to access this resource."

    def has_permission(self, request, view):
        user = _authenticated_user(request)
        return bool(user and getattr(user, "role", None) == self.role)

class IsCustomer(IsAuthenticatedRole):
    message = "Only customers can access this resource."
    role = "CUSTOMER"

class IsAgent(IsAuthenticatedRole):
    message = "Only agents can access this resource."
    role = "AGENT"

class IsAdmin(BasePermission):
    message = "Only staff administrators can access this resource."

    def has_permission(self, request, view):
        return _is_admin(_authenticated_user(request))

class IsAgentOrAdmin(BasePermission):
    message = "Only agents or staff administrators can access this resource."

    def has_permission(self, request, view):
        user = _authenticated_user(request)
        return bool(user and (getattr(user, "role", None) == "AGENT"
                              or _is_admin(user)))

class IsOwnerOrAdmin(BasePermission):
    """Allow access to an object's owner or a staff administrator.

    Supported ownership attributes are user, customer, owner and their
    corresponding user_id, customer_id, owner_id fields.
    """
    message = "You can access only your own resource."

    def has_permission(self, request, view):
        return _authenticated_user(request) is not None

    def has_object_permission(self, request, view, obj):
        user = _authenticated_user(request)
        if not user:
            return False
        if _is_admin(user):
            return True
        owner_ids = (
            getattr(obj, "user_id", None),
            getattr(obj, "customer_id", None),
            getattr(obj, "owner_id", None),
            getattr(getattr(obj, "user", None), "pk", None),
            getattr(getattr(obj, "customer", None), "pk", None),
            getattr(getattr(obj, "owner", None), "pk", None),
        )
        return user.pk in owner_ids
