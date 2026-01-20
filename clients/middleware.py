from django.shortcuts import redirect
from django_tenants.utils import get_tenant_model
from django.http import Http404
import logging

logger = logging.getLogger(__name__)
from django.utils import timezone
from django_tenants.utils import get_public_schema_name
from django.contrib import messages

from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.http import HttpResponseForbidden
from django.urls import resolve
from django.contrib.auth import logout
from django.conf import settings
from django.utils.timezone import now
from.models import UserRequestLog
from django.urls import Resolver404


from django.contrib.auth import get_user_model
from accounts.models import UserProfile  
User = get_user_model() 

from django.core.exceptions import PermissionDenied
from django.urls import reverse



class BlockStudentByNamespaceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.deny_namespaces = set(getattr(settings, "STUDENT_DENY_NAMESPACES", []))
        self.allow_url_names = set(getattr(settings, "STUDENT_ALLOW_URL_NAMES", []))
        self.allow_superuser = getattr(settings, "STUDENT_ALLOW_SUPERUSER", True)
        self.redirect_url_name = getattr(settings, "STUDENT_REDIRECT_URL_NAME", None)

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):  
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        is_student = getattr(user, "role", None) == "student"
        if not is_student or (self.allow_superuser and user.is_superuser):
            return None
        rm = getattr(request, "resolver_match", None)
        if not rm:
            return None
        if rm.view_name in self.allow_url_names:
            return None
        if rm.namespace and rm.namespace in self.deny_namespaces:
            if self.redirect_url_name:
                return redirect(reverse(self.redirect_url_name))
            raise PermissionDenied("Students are not allowed here.")

        return None


class CustomTenantAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        tenant = getattr(request, 'tenant', None)
        schema_name = getattr(connection, 'schema_name', None)
        is_public_tenant = tenant and tenant.schema_name == get_public_schema_name()

        if schema_name:
            request.session.cookie_name = f'sessionid_{schema_name}'

        user = request.user

        # If it's the public schema, prevent redirect loop
        if is_public_tenant:
            if user.is_authenticated:
                logout(request)
                request.session.flush()
            return  # allow access to public schema

        if user.is_authenticated and tenant:
            user_tenant = getattr(user, 'tenant', None)

            if user.is_superuser:
                return

            if not user_tenant or user_tenant.schema_name != tenant.schema_name:
                logout(request)
                request.session.flush()
                messages.error(request, "You are not allowed to log in to this tenant.")

                if user_tenant:
                    return redirect(f'https://www.{user_tenant.schema_name}.bnova.pro')
                return redirect('https://www.bnova.pro')
