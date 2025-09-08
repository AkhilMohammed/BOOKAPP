from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """
    Custom permission to only allow admin users to access certain views.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated and is an admin

        return bool(request.user and request.user.is_authenticated and request.user.user_type == 'admin')
    
    
class IsCustomerUser(BasePermission):
    """
    Custom permission to only allow customer users to access certain views.
    """  
    def has_permission(self, request, view):
        # Check if the user is authenticated and is a customer  

        return bool(request.user and request.user.is_authenticated and request.user.user_type == 'customer')
     

class IsVendorUser(BasePermission):
    """
    Custom permission to only allow vendor users to access certain views.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated and is a vendor

        return bool(request.user and request.user.is_authenticated and request.user.user_type == 'vendor')
    
    
class IsSuperAdminUser(BasePermission):
    """
    Custom permission to only allow super admin users to access certain views.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated and is a super admin

        return bool(request.user and request.user.is_authenticated and request.user.user_type == 'superadmin')
    
    
class IsDeliveryUser(BasePermission):
    """
    Custom permission to only allow delivery users to access certain views.
    """ 
    def has_permission(self, request, view):
        # Check if the user is authenticated and is a delivery user

        return bool(request.user and request.user.is_authenticated and request.user.user_type == 'delivery')
    


