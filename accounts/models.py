from cloudinary.models import CloudinaryField
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg


class Profile(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ADMIN = "admin", "Admin"
        SUPER_ADMIN = "super_admin", "Super Admin"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = CloudinaryField("avatar", folder="skillswap/avatars", blank=True)
    bio = models.TextField(max_length=500, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    @property
    def is_admin(self):
        return not self.is_banned and self.role in {
            self.Role.ADMIN,
            self.Role.SUPER_ADMIN,
        }

    @property
    def is_super_admin(self):
        return not self.is_banned and self.role == self.Role.SUPER_ADMIN

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

