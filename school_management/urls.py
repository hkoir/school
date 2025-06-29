
from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
 
from clients.views import tenant_expire_check




app_name = 'school_management'

urlpatterns = [
   path('create_image_gallery/', views.manage_image_gallery, name='create_image_gallery'),    
   path('update_image_gallery/<int:id>/', views.manage_image_gallery, name='update_image_gallery'),    
   path('delete_school/<int:id>/', views.delete_image_gallery, name='delete_image_gallery'),  
   path('image_list/', views.image_list, name='image_list'),

   path('create_school/', views.manage_school, name='create_school'),    
   path('update_school/<int:id>/', views.manage_school, name='update_school'),    
   path('delete_school/<int:id>/', views.delete_school, name='delete_school'),  

    path('create_faculty/', views.manage_faculty, name='create_faculty'),    
    path('update_faculty/<int:id>/', views.manage_faculty, name='update_faculty'),    
    path('delete_faculty/<int:id>/', views.delete_faculty, name='delete_faculty'), 
    
    path('create_class/', views.manage_class, name='create_class'),    
    path('update_class/<int:id>/', views.manage_class, name='update_class'),    
    path('delete_class/<int:id>/', views.delete_class, name='delete_class'),  
   
   path('create_class_assignment/', views.manage_class_assignment, name='create_class_assignment'),    
   path('update_class_assignment/<int:id>/', views.manage_class_assignment, name='update_class_assignment'),    
   path('delete_class_assignment/<int:id>/', views.delete_class_assignment, name='delete_class_assignment'),  
    
   path('create_subject_assignment/', views.manage_subject_assignment, name='create_subject_assignment'),    
   path('update_subject_assignment/<int:id>/', views.manage_subject_assignment, name='update_subject_assignment'),    
   path('delete_subject_assignment/<int:id>/', views.delete_subject_assignment, name='delete_subject_assignment'),    


    path('create_section/', views.manage_section, name='create_section'),    
    path('update_section/<int:id>/', views.manage_section, name='update_section'),    
    path('delete_section/<int:id>/', views.delete_section, name='delete_section'),  

    path('create_class_room/', views.manage_class_room, name='create_class_room'),    
    path('update_class-room/<int:id>/', views.manage_class_room, name='update_class_room'),
    path('delete_section/<int:id>/', views.delete_class_room, name='delete_class_room'),  
  
    path('create_subject/', views.manage_subject, name='create_subject'),    
    path('update_subject/<int:id>/', views.manage_subject, name='update_subject'),
    path('delete_subject/<int:id>/', views.delete_subject, name='delete_subject'),  

    path('create_schedule/', views.manage_schedule, name='create_schedule'),    
    path('update_schedule/<int:id>/', views.manage_schedule, name='update_schedule'),
    path('delete_schedule/<int:id>/', views.delete_schedule, name='delete_schedule'),  

    path('create_teaching_assignment/', views.manage_teaching_assignment, name='create_teaching_assignment'),    
    path('update_teaching_assignment/<int:id>/', views.manage_teaching_assignment, name='update_teaching_assignment'),
    path('delete_teaching_assignment/<int:id>/', views.delete_teaching_assignment, name='delete_teaching_assignment'),  
  
    path('create_image_gallery/', views.manage_image_gallery, name='create_image_gallery'),    
    path('update_image_gallery/<int:id>/', views.manage_image_gallery, name='update_image_gallery'),
    path('delete_image_gallery/<int:id>/', views.delete_image_gallery, name='delete_image_gallery'),  
  
  
   
  
   
  
  
  
  
]