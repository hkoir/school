
from .models import UserProfile
from messaging.models import Notification
from students.models import Student
from teachers.models import Teacher
from core.models import Employee
from django.db.utils import ProgrammingError
from django_tenants.utils import get_tenant_model
from django_tenants.utils import get_tenant
from clients.models import Tenant
from messaging.models import CommunicationMessage
from messaging.models import Conversation
from school_management.models import School


def user_info(request):
    profile_picture_url = None
    student = None
    teacher = None
    employee = None
    school_logo_url = 'Unknown'
    school_name = 'None'
    tenant_photo_url = None
    school_address=None
    school_website=None

    school = School.objects.first()


    if request.user.is_authenticated:
        try:
            current_client = get_tenant(request)
   
            if current_client.schema_name == 'public':
                return {
                    'user_info': request.user.username,
                    'profile_picture_url': profile_picture_url,
                    'school_logo_url': school_logo_url,
                    'school_name': school_name,
                }

            tenant_instance = Tenant.objects.filter(tenant=current_client).first()
            if tenant_instance and tenant_instance.logo:
                school_logo_url = tenant_instance.logo.url
                school_name = tenant_instance.name
                school_address = tenant_instance.address
                school_website = current_client


        except ProgrammingError:
            pass
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error in user_info context processor: {e}")

    return {
        'user_info': request.user.username if request.user.is_authenticated else None,
        'profile_picture_url': profile_picture_url,
        'school_logo_url': school_logo_url,
        'school_name': school_name,
        'school':school,
        'school_address': school_address,
        'school_website': f"http://www.{school_website}.bnova.pro",
    }



def tenant_schema(request):
    schema_name = getattr(request.tenant, 'schema_name', 'public')
    return {'schema_name': schema_name}


from collections import defaultdict
from django.db.models import Q

def unread_notifications(request):
    current_client = get_tenant(request)
    if current_client.schema_name == 'public' or not request.user.is_authenticated:
        return {
            'unread_notifications': [],
            'unread_chat_messages': [],
            'unread_chat_messages_count': 0,
            'unread_per_conversation': {}
        }

    # Start with all unread notifications
    notifications = Notification.objects.filter(is_read=False)

    # Filter notifications belonging to the logged-in user, either directly or via related student/teacher
    if request.user.role == "student":
        notifications = notifications.filter(
            Q(student__user=request.user) | Q(user=request.user)
        )
    elif request.user.role == "teacher":
        notifications = notifications.filter(
            Q(teacher__user=request.user) | Q(user=request.user)
        )
    else:
        notifications = notifications.filter(user=request.user)

    # Group conversations for the current user
    group_conversations = Conversation.objects.filter(participants=request.user, is_group=True)

    # Count unread messages per conversation excluding messages sent by the user or already read by the user
    comm_messages = CommunicationMessage.objects.filter(
        conversation__in=group_conversations
    ).exclude(
        sender=request.user
    ).exclude(
        read_statuses__user=request.user
    )

    unread_map = defaultdict(int)
    for msg in comm_messages:
        unread_map[msg.conversation_id] += 1

    return {
        'unread_notifications': notifications,
        'unread_chat_messages': group_conversations,
        'unread_chat_messages_count': sum(unread_map.values()),
        'unread_per_conversation': dict(unread_map),
    }
