from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile
from notifications.models import Notification # type: ignore
from notifications.views import send_notification_to_user # type: ignore

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        
        # Create welcome notification
        notification = Notification.objects.create(
            user=instance,
            title="Welcome to ChatApp!",
            message=f"Welcome {instance.full_name}! Start chatting with your friends.",
            notification_type='welcome'
        )
        
        # Send real-time notification
        send_notification_to_user(instance.id, {
            'id': str(notification.id),
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'created_at': notification.created_at.isoformat()
        })

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()