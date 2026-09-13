from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.views.auth import LogoutView, MobileTokenRefreshView, RequestOTPView, VerifyOTPView
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
from apps.views.product import ProductViewSet
from apps.views.user import FollowToggleView, MeView, UserPublicDetailView

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'reels', ReelViewSet, basename='reel')
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    # Auth & User
    path('auth/send-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/refresh/', MobileTokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('users/me/', MeView.as_view(), name='me'),
    path('users/<uuid:id>/', UserPublicDetailView.as_view(), name='user-detail'),
    path('users/<uuid:id>/follow/', FollowToggleView.as_view(), name='follow-toggle'),

    # Listings & Categories
    path('listings/map/', ListingViewSet.as_view({'get': 'map'}), name='listing-map'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('favorites/', FavoriteListView.as_view(), name='favorite-list'),
    path('reports/', ReportCreateView.as_view(), name='report-create'),

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
