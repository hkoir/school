from django import forms
from.models import ManagementMessage
from .models import CommunicationMessage,Conversation
from accounts.models import CustomUser


class ManagementMessageForm(forms.ModelForm):
    class Meta:
        model = ManagementMessage
        exclude=['user']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'columns': 6,
                'placeholder': 'Enter your message here'
            })
        }




class CommunicationMessageForm(forms.ModelForm):
    recipients = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=True,
        label='To'
    )

    class Meta:
        model = CommunicationMessage
        fields = ['recipients', 'subject', 'body','image','video']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'style':'height:75px', 'class': 'form-control'}),
        }



class ReplyMessageForm(forms.ModelForm):
    class Meta:
        model = CommunicationMessage
        fields = ['body','image','video']
        widgets = {
            'body': forms.Textarea(attrs={'class':'form-control','style':'height:75px','placeholder': 'Write your reply...'}),
        }






class ConversationFilterForm(forms.Form):    
    conversation = forms.ChoiceField(
        required=False,
        label='Filter Conversations',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        choices = [
            ('', 'All Conversations'),
            ('all_received', 'All Received'),
            ('all_sent', 'All Sent'),
            ('groups', 'All Groups'),
            ('private', 'All Private Chats'),
        ]

        groups = Conversation.objects.filter(participants=user, is_group=True)
        for group in groups:
            label = group.name or 'Unnamed Group'
            choices.append((f'group_{group.id}', f"Group: {label}"))

        private_convos = Conversation.objects.filter(participants=user, is_group=False).prefetch_related('participants')
        user_set = set()
        for convo in private_convos:
            others = convo.participants.exclude(id=user.id)
            for other in others:
                user_set.add((other.id, other.get_full_name() or other.username))

        for uid, uname in sorted(user_set, key=lambda x: x[1].lower()):
            choices.append((f'user_{uid}', f"Chat with: {uname}"))

        self.fields['conversation'].choices = choices







