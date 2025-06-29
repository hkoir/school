
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('admin/', admin.site.urls),
    path('select2/', include('django_select2.urls')),
    path('', include('accounts.urls', namespace='accounts')),
    path("accounts/", include("django.contrib.auth.urls")), 
    path('clients/',include('clients.urls',namespace='clients')),  
    path('attendance/',include('attendance.urls',namespace='attendance')),
    path('messaging/',include('messaging.urls',namespace='messaging')),  
    path('payments/',include('payments.urls',namespace='payments')),  
    path('performance/',include('performance.urls',namespace='performance')),  
    path('results/',include('results.urls',namespace='results')),  
    path('school_management/',include('school_management.urls',namespace='school_management')),  
    path('students/',include('students.urls',namespace='students')),  
    path('teachers/',include('teachers.urls',namespace='teachers')),  
    path('core/',include('core.urls',namespace='core')),  
    path('student_portal/',include('student_portal.urls',namespace='student_portal')),  

    path('leavemanagement/',include('leavemanagement.urls',namespace='leavemanagement')),
    path('finance/',include('finance.urls',namespace='finance')),
   path('inventory/',include('inventory.urls',namespace='inventory')),


]






if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
