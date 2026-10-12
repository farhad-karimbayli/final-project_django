from django.urls import path

from . import views


urlpatterns = [
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("profile/<str:username>/", views.profile_detail, name="profile_detail"),
    path("mentors/", views.mentor_list, name="mentor_list"),
    path("manage/", views.user_management, name="user_management"),
    path("manage/<int:user_id>/ban/", views.toggle_ban, name="toggle_ban"),
    path("manage/<int:user_id>/admin/", views.toggle_admin, name="toggle_admin"),
]

