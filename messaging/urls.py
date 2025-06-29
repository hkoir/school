
from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
 
from clients.views import tenant_expire_check




app_name = 'messaging'

urlpatterns = [
    path('', tenant_expire_check, name='tenant_expire_check'),
    path("notifications/mark-as-read/<int:notification_id>/", views.mark_notification_read_view, name="mark_notification_as_read"),

    path('create_manage_management_message/', views.manage_management_message, name='create_management_message'),    
    path('update_management_message/<int:id>/', views.manage_management_message, name='update_management_message'),    
    path('delete_management_message/<int:id>/', views.delete_management_message, name='delete_management_message'),  

    path("inbox/", views.inbox, name="inbox"),
    path("inbox/<int:pk>/", views.inbox, name="inbox"),
    path('send-message/', views.send_message, name='send_message'),   
    path("create_group/", views.create_group_conversation, name="create_group"),   
    path('group/<int:pk>/add-participants/', views.add_participants, name='add_participants'),
    path('group/<int:pk>/remove-participants/', views.remove_participants, name='remove_participants'),
    path('message/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('message/<int:message_id>/edit/', views.edit_message, name='edit_message'),



  
]
