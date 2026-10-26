from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "is_banned", "bio")
    list_filter = ("role", "is_banned")
    search_fields = ("user__username",)

