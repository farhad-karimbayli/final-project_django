from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from bookings.models import LessonRequest
from offers.models import Offer


class Review(models.Model):
    lesson_request = models.OneToOneField(
        LessonRequest, on_delete=models.CASCADE, related_name="review"
    )
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="reviews")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews_written")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(max_length=1200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        errors = {}
        if self.lesson_request_id:
            if self.lesson_request.status != LessonRequest.Status.COMPLETED:
                errors["lesson_request"] = "A review requires a completed lesson."
            if self.author_id and self.author_id != self.lesson_request.requester_id:
                errors["author"] = "Only the lesson requester can write this review."
            if self.offer_id and self.offer_id != self.lesson_request.offer_id:
                errors["offer"] = "The review must belong to the requested offer."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.rating}/5 — {self.offer}"

