from django.urls import path

from api.apps.users.views import (
    UserRegistrationView, UserView, CustomTokenObtainPairView, CustomTokenRefreshView, LogoutView, LogoutAllView,
    DepositView, ResetDepositView
)


urlpatterns = [
    path("", UserRegistrationView.as_view(), name="create_user"),
    path("me/", UserView.as_view(), name="user_view"),
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("login/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("logout/all/", LogoutAllView.as_view(), name="logout_all"),
    path("deposit/", DepositView.as_view(), name="deposit"),
    path("reset-deposit/", ResetDepositView.as_view(), name="reset_deposit"),
]
