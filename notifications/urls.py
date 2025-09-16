from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('unread/', views.UnreadNotificationListView.as_view(), name='unread_notifications'),
    path('count/', views.notification_count, name='notification_count'),
    path('<uuid:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('<uuid:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]