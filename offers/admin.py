from django.contrib import admin

from .models import Category, Favorite, Offer


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "status", "created_at")
    list_filter = ("status", "category", "level", "lesson_format")
    search_fields = ("title", "author__username")


admin.site.register(Favorite)

