

from django.contrib.auth import get_user_model
from django_tenants.utils import get_tenant_model
from django.core.exceptions import PermissionDenied
from clients.models import Client
User = get_user_model()
from django.contrib.auth.backends import ModelBackend
UserModel = get_user_model()



class TenantAuthenticationBackend(ModelBackend):   
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = None
        if username is None or password is None:
            return None
        try:         
            user = UserModel.objects.get(phone_number=username)
        except UserModel.DoesNotExist:
            try:              
                user = UserModel.objects.get(email=username)
            except UserModel.DoesNotExist:
                try:                   
                    user = UserModel.objects.get(username=username)
                except UserModel.DoesNotExist:
                    return None
        if user and user.check_password(password):
            return user
        return None

        
