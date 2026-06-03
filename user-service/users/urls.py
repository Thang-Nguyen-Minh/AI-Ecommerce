from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [

    # ── Health ──────────────────────────────────
    path('users/health/', views.health_check),

    # ── Auth ────────────────────────────────────
    path('auth/login/',    views.LoginView.as_view()),
    path('auth/register/', views.RegisterView.as_view()),
    path('auth/logout/',   views.LogoutView.as_view()),
    path('auth/refresh/',  TokenRefreshView.as_view()),

    # ── Tôi ─────────────────────────────────────
    path('users/me/',                          views.MeView.as_view()),
    path('users/me/change-password/',          views.ChangePasswordView.as_view()),
    path('users/me/addresses/',                views.AddressListView.as_view()),
    path('users/me/addresses/<int:pk>/',       views.AddressDetailView.as_view()),
    path('users/me/addresses/<int:pk>/set-default/', views.SetDefaultAddressView.as_view()),

    # ── Admin ────────────────────────────────────
    path('users/',         views.UserListView.as_view()),
    path('users/stats/',   views.user_stats),
    path('users/<int:pk>/', views.UserDetailView.as_view()),
]