from django.contrib import admin
from.models import Notification,ManagementMessage,Message,Conversation,CommunicationMessage,MessageReadStatus
from.models import TenantEmailConfig,TenantSMSConfig,GlobalSMSConfig


admin.site.register(Notification)
admin.site.register(ManagementMessage)
admin.site.register(Message)
admin.site.register(Conversation)
admin.site.register(CommunicationMessage)
admin.site.register(MessageReadStatus)


admin.site.register(TenantEmailConfig)
admin.site.register(GlobalSMSConfig)
admin.site.register(TenantSMSConfig)
