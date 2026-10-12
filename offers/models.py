from cloudinary.models import CloudinaryField
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Avg


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Offer(models.Model):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    class Format(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        PUBLISHED = "published", "Published"
        REJECTED = "rejected", "Rejected"

    title = models.CharField(max_length=160)
    description = models.TextField(max_length=3000)
    image = CloudinaryField("image", folder="skillswap/offers", blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="offers")
    level = models.CharField(max_length=20, choices=Level.choices)
    lesson_format = models.CharField(max_length=10, choices=Format.choices)
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(15)])
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="offers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    rejection_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def average_rating(self):
        value = self.reviews.aggregate(average=Avg("rating"))["average"]
        return round(value, 1) if value is not None else None

    @property
    def ratings_count(self):
        return self.reviews.count()

    @property
    def completed_lessons_count(self):
        return self.lesson_requests.filter(status="completed").count()


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "offer"], name="unique_user_favorite")
        ]

    def __str__(self):
        return f"{self.user} — {self.offer}"

