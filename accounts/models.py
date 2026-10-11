from cloudinary.models import CloudinaryField
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = CloudinaryField("avatar", folder="skillswap/avatars", blank=True)
    bio = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return self.user.username

    @property
    def average_rating(self):
        value = self.user.offers.aggregate(average=Avg("reviews__rating"))["average"]
        return round(value, 1) if value is not None else None

    @property
    def published_offers_count(self):
        return self.user.offers.filter(status="published").count()

    @property
    def completed_lessons_count(self):
        return self.user.offers.filter(lesson_requests__status="completed").count()

