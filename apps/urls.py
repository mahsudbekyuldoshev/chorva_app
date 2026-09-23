from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.views.auth import LogoutView, MobileTokenRefreshView, RequestOTPView, VerifyOTPView
from apps.views.banner import BannerListView, BannerViewIncrementView
from apps.views.chat import ConversationListCreateView, MessageListCreateView
from apps.views.chat_mobile import ChatListCreateView, ChatMarkReadView, ChatMessageListCreateView
from apps.views.favourite import FavouriteListView, FavouriteToggleView
from apps.views.listing import (
    CategoryListView,
    FavoriteListView,
    ListingViewSet,
    ReelViewSet,
    ReportCreateView,
)
from apps.views.media import MediaPresignView
from apps.views.notification import NotificationListView, NotificationMarkReadView
from apps.views.notification_extra import NotificationMarkAllReadView, NotificationUnreadCountView
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
    path('favourites/', FavouriteListView.as_view(), name='favourite-list-mobile'),
    path('favourites/<uuid:product_id>/', FavouriteToggleView.as_view(), name='favourite-toggle'),
    path('favorites/', FavoriteListView.as_view(), name='favorite-list'),
    path('reports/', ReportCreateView.as_view(), name='report-create'),
    path('media/presign/', MediaPresignView.as_view(), name='media-presign'),
    path('banners/', BannerListView.as_view(), name='banner-list'),
    path('banners/<uuid:pk>/view/', BannerViewIncrementView.as_view(), name='banner-view'),

    # Chat
    path('conversations/', ConversationListCreateView.as_view(), name='conversation-list'),
    path('conversations/<uuid:conversation_id>/messages/', MessageListCreateView.as_view(), name='message-list'),
    path('chats/', ChatListCreateView.as_view(), name='chat-list'),
    path('chats/<uuid:conversation_id>/messages/', ChatMessageListCreateView.as_view(), name='chat-messages'),
    path('chats/<uuid:conversation_id>/read/', ChatMarkReadView.as_view(), name='chat-read'),

    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/unread-count/', NotificationUnreadCountView.as_view(), name='notification-unread-count'),
    path('notifications/read-all/', NotificationMarkAllReadView.as_view(), name='notification-read-all'),
    path('notifications/<uuid:pk>/read/', NotificationMarkReadView.as_view(), name='notification-read'),
    path('plans/', PlanListView.as_view(), name='plan-list'),

    # Router URLs
    path('', include(router.urls)),
]
