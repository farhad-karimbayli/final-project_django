from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from accounts import views as account_views


urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/register/", account_views.register, name="register"),
    path("accounts/", include("accounts.urls")),
    path("requests/", include("bookings.urls")),
    path("reviews/", include("reviews.urls")),
    path("", include("offers.urls")),
]

