from django.urls import path

from . import views


urlpatterns = [
    path("", views.my_requests, name="my_requests"),
    path("offer/<int:offer_id>/send/", views.send_request, name="send_request"),
    path("<int:pk>/<str:action>/", views.update_request_status, name="update_request_status"),
]

