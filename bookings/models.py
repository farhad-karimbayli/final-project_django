from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from offers.models import Offer


class LessonRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="lesson_requests")
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_requests")
    message = models.TextField(max_length=700, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["offer", "requester"],
                condition=Q(status__in=["pending", "accepted"]),
                name="unique_active_lesson_request",
            )
        ]

    def clean(self):
        if self.offer_id and self.requester_id and self.offer.author_id == self.requester_id:
            raise ValidationError("You cannot request a lesson from yourself.")
        if self.offer_id and self.offer.status != Offer.Status.PUBLISHED:
            raise ValidationError("Lesson requests are available only for published offers.")

    def __str__(self):
        return f"{self.requester} → {self.offer} ({self.get_status_display()})"

