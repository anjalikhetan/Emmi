from rest_framework import permissions
from django.conf import settings
from api.plans.models import Plan


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


class IsPlanOwner(permissions.BasePermission):
    """
    Permission to only allow the owner of a plan to access it and its workouts.
    """
    def has_permission(self, request, view):
        # Check if plan_id is in the URL kwargs
        plan_id = view.kwargs.get('plan_id')
        if not plan_id:
            return False
        
        # Check if the plan exists and belongs to the user
        return Plan.objects.filter(
            id=plan_id, 
            user=request.user
        ).exists()
    
    def has_object_permission(self, request, view, obj):
        # For workout detail view, check if the plan belongs to the user
        if hasattr(obj, 'plan'):
            return str(obj.plan.user.id) == str(request.user.id)
        # For plan detail view
        return str(obj.user.id) == str(request.user.id)