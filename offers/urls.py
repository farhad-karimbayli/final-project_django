from django.urls import path

from . import views


urlpatterns = [
    path("", views.explore, name="offer_explore"),
    path("popular/", views.popular, name="offer_popular"),
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_update, name="category_update"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    path("categories/<slug:slug>/", views.category_offers, name="category_offers"),
    path("offers/create/", views.offer_create, name="offer_create"),
    path("offers/mine/", views.my_offers, name="my_offers"),
    path("offers/favorites/", views.favorites, name="favorites"),
    path("offers/moderation/", views.moderation_queue, name="moderation_queue"),
    path("offers/<int:pk>/", views.offer_detail, name="offer_detail"),
    path("offers/<int:pk>/edit/", views.offer_update, name="offer_update"),
    path("offers/<int:pk>/delete/", views.offer_delete, name="offer_delete"),
    path("offers/<int:pk>/favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("offers/<int:pk>/moderate/", views.moderate_offer, name="moderate_offer"),
]

