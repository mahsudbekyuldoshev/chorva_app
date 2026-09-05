from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.views.auth import RequestOTPView, VerifyOTPView
from apps.views.chat import ConversationListCreateView, MessageListCreateView
from apps.views.listing import (
    CategoryListView,
    FavoriteListView,
    ListingViewSet,
    ReelViewSet,
    ReportCreateView,
)
from apps.views.notification import NotificationListView, NotificationMarkReadView
from apps.views.plan import PlanListView
from apps.views.user import FollowToggleView, MeView, UserPublicDetailView

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'reels', ReelViewSet, basename='reel')

urlpatterns = [
    # Auth & User
    path('auth/request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('users/<uuid:pk>/', UserPublicDetailView.as_view(), name='user-detail'),
    path('users/<uuid:id>/follow/', FollowToggleView.as_view(), name='follow-toggle'),

    # Listings & Categories
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('favorites/', FavoriteListView.as_view(), name='favorite-list'),
    path('reports/', ReportCreateView.as_view(), name='report-create'),
    path('listings/map/', ListingViewSet.as_view({'get': 'map'}), name='listing-map'),

    # Chat
    path('conversations/', ConversationListCreateView.as_view(), name='conversation-list'),
    path('conversations/<uuid:conversation_id>/messages/', MessageListCreateView.as_view(), name='message-list'),

    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<uuid:pk>/read/', NotificationMarkReadView.as_view(), name='notification-read'),
    path('plans/', PlanListView.as_view(), name='plan-list'),

    # Router URLs
    path('', include(router.urls)),
]
