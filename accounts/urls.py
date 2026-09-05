from django.urls import path

from .views import RegisterView,ProfileView,LogoutView,ChangePasswordView,ProfileUpdateView,VerifyEmailView


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("change-password/",ChangePasswordView.as_view(),name="change_password",),
    path("profile/update/",ProfileUpdateView.as_view(),name="profile_update",),
    path("verify-email/<int:user_id>/<str:token>/",VerifyEmailView.as_view(),name="verify_email",),
]