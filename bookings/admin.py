from django.contrib import admin

from .models import LessonRequest


@admin.register(LessonRequest)
class LessonRequestAdmin(admin.ModelAdmin):
    list_display = ("offer", "requester", "status", "created_at")
    list_filter = ("status",)

