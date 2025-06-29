from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from.models import  Notification
from django.contrib import messages
from students.models import Student
from.models import Message
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from .models import Notification
from django.views.decorators.http import require_POST
from messaging.models import ManagementMessage
from.forms import ManagementMessageForm
from django.core.paginator import Paginator

# def create_notification(user,notification_type, message):   
#     Notification.objects.create(user,message=message,notification_type=notification_type)






@login_required
#@require_POST  # Only allow POST requests
def mark_notification_read_view(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({"success": True}) 
    except Notification.DoesNotExist:
        return JsonResponse({"success": False, "error": "Notification not found"}, status=404)



@login_required
def manage_management_message(request, id=None):  
    instance = get_object_or_404(ManagementMessage, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = ManagementMessageForm(request.POST or None, request.FILES or None, instance=instance)

    max_messages = 6 
    message_count = ManagementMessage.objects.all().count()
    if message_count >= max_messages:
        messages.error(request, "You have reached the maximum limit of messages.")
        return redirect('messaging:create_management_message')  

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)     
        form_intance.user=request.user  
        form_intance.save()              
        messages.success(request, message_text)
        return redirect('messaging:create_management_message')  
    else:
        print(form.errors)

    datas = ManagementMessage.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = ManagementMessageForm(instance=instance)
    return render(request, 'messaging/manage_management_message.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_management_message(request, id):
    instance = get_object_or_404(ManagementMessage, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('messaging:create_management_message')    

    messages.warning(request, "Invalid delete request!")
    return redirect('messaging:create_management_message')  




#=================================== Communicationmmessages ====================

from .models import CommunicationMessage,Conversation,MessageReadStatus
from .forms import CommunicationMessageForm
from accounts.models import CustomUser
from django.db.models import OuterRef, Subquery, Q,Count
from .forms import ReplyMessageForm

def get_or_create_conversation(user1, user2):  
    user1, user2 = sorted([user1, user2], key=lambda u: u.id)

    conversation = Conversation.objects.filter(is_group=False, participants=user1)\
                                       .filter(participants=user2)\
                                       .distinct().first()

    if not conversation:
        conversation = Conversation.objects.create(is_group=False)
        conversation.participants.set([user1, user2])
        conversation.save()

    return conversation





@login_required
def send_message(request):
    if request.method == 'POST':
        form = CommunicationMessageForm(request.POST, request.FILES)
        if form.is_valid():
            recipients = form.cleaned_data['recipients']
            subject = form.cleaned_data['subject']
            body = form.cleaned_data['body']
            image = form.cleaned_data.get('image')  # use get to avoid KeyError
            video = form.cleaned_data.get('video')

            for recipient in recipients:
                conversation = get_or_create_conversation(request.user, recipient)
                CommunicationMessage.objects.create(
                    sender=request.user,
                    recipient=recipient,
                    subject=subject,
                    body=body,
                    conversation=conversation,
                    image=image if image else None,
                    video=video if video else None
                )
            return redirect('messaging:inbox')
    else:
        form = CommunicationMessageForm()
    
    return render(request, 'messaging/send_message.html', {'form': form})




@login_required
def create_group_conversation(request):
    if request.method == "POST":
        name = request.POST.get("name")
        user_ids = request.POST.getlist("participants")
        participants = CustomUser.objects.filter(id__in=user_ids)
        if participants.exists():
            conversation = Conversation.objects.create(name=name, is_group=True)
            conversation.participants.set(participants)
            conversation.participants.add(request.user)
            return redirect("messaging:group_conversation_detail", pk=conversation.pk)
    users = CustomUser.objects.exclude(id=request.user.id)
    return render(request, "messaging/create_group_conversation.html", {"users": users})




@login_required
def add_participants(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, is_group=True)
    if request.method == "POST":
        user_ids = request.POST.getlist("participants")
        users = CustomUser.objects.filter(id__in=user_ids).exclude(id__in=conversation.participants.all())
        conversation.participants.add(*users)
        return redirect('messaging:group_conversation_detail', pk=conversation.pk)
    available_users = CustomUser.objects.exclude(id__in=conversation.participants.all())
    return render(request, "messaging/add_participants.html", {
        "conversation": conversation,
        "available_users": available_users
    })


@login_required
def remove_participants(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, is_group=True)
    if request.method == "POST":
        user_ids = request.POST.getlist("participants")
        users = CustomUser.objects.filter(id__in=user_ids).exclude(id=request.user.id)
        conversation.participants.remove(*users)
        return redirect('messaging:group_conversation_detail', pk=conversation.pk)
    current_participants = conversation.participants.exclude(id=request.user.id)
    return render(request, "messaging/remove_participants.html", {
        "conversation": conversation,
        "current_participants": current_participants
    })




@login_required
def edit_message(request, message_id):
    message = get_object_or_404(CommunicationMessage, id=message_id, sender=request.user)
    if request.method == 'POST':
        form = ReplyMessageForm(request.POST, request.FILES, instance=message)
        if form.is_valid():
            form.save()
            return redirect('messaging:group_conversation_detail', pk=message.conversation.id)
    else:
        form = ReplyMessageForm(instance=message)
    return render(request, 'messaging/edit_message.html', {'form': form, 'message': message})


@login_required
def delete_message(request, message_id):
    message = get_object_or_404(CommunicationMessage, id=message_id, sender=request.user) 
    if request.method == 'POST':
        conversation_id = message.conversation.id
        message.delete()        
        return redirect('messaging:group_conversation_detail', pk=conversation_id)
    return render(request, 'messaging/confirm_delete.html', {'message': message})





from .forms import ConversationFilterForm
from collections import defaultdict
from django.db import models

@login_required
def inbox(request, pk=None):
    user = request.user
    filter_form = ConversationFilterForm(request.GET or None, user=user)
    filter_value = request.GET.get('conversation', '')

    qs = CommunicationMessage.objects.filter(conversation__participants=user)

    # Apply filtering based on dropdown
    if filter_value == 'all_received':
        qs = qs.filter(recipient=user)
    elif filter_value == 'all_sent':
        qs = qs.filter(sender=user)
    elif filter_value == 'groups':
        qs = qs.filter(conversation__is_group=True)
    elif filter_value.startswith('group_'):
        group_id = filter_value.split('_')[1]
        qs = qs.filter(conversation__id=group_id)
    elif filter_value == 'private':
        qs = qs.filter(conversation__is_group=False)
    elif filter_value.startswith('user_'):
        user_id = filter_value.split('_')[1]
        qs = qs.filter(
            conversation__is_group=False,
            conversation__participants__id=user_id
        )

    # Show only one message per conversation (latest)
    latest_msgs = (
        qs
        .select_related("sender", "conversation", "reply_to")
        .order_by("conversation", "-timestamp")
        .distinct("conversation")
    )

    unread_counts = (
        CommunicationMessage.objects
        .filter(is_read=False, recipient=user)
        .values('conversation')
        .annotate(count=models.Count('id'))
    )
    unread_count_map = {item['conversation']: item['count'] for item in unread_counts}

    paginator = Paginator(latest_msgs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Handle selected conversation view and reply
    selected_conversation = None
    if pk:
        selected_conversation = get_object_or_404(Conversation, pk=pk, participants=user)
        selected_conversation.messages.exclude(sender=user).filter(is_read=False).update(is_read=True)

        if request.method == "POST":
            form = ReplyMessageForm(request.POST, request.FILES)
            if form.is_valid():
                msg = form.save(commit=False)
                msg.sender = user
                msg.conversation = selected_conversation
                if not selected_conversation.is_group:
                    recipient_qs = selected_conversation.participants.exclude(id=user.id)
                    if recipient_qs.exists():
                        msg.recipient = recipient_qs.first()

                reply_to_id = request.POST.get('reply_to')
                if reply_to_id:
                    try:
                        reply_msg = CommunicationMessage.objects.get(id=reply_to_id, conversation=selected_conversation)
                        msg.reply_to = reply_msg
                    except CommunicationMessage.DoesNotExist:
                        pass

                msg.save()
                return redirect("messaging:inbox", pk=pk)
        else:
            form = ReplyMessageForm()
    else:
        form = ReplyMessageForm()

    return render(request, "messaging/chat_two_pane.html", {
        "page_obj": page_obj,
        "selected_conversation": selected_conversation,
        "form": form,
        "filter_form": filter_form,
	"unread_count_map": unread_count_map,
    })

