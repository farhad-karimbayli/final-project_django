from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from bookings.models import LessonRequest
from offers.models import Category, Offer

from .models import Review


class ReviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.get(name="Design")
        cls.mentor = User.objects.create_user("mentor", password="pass")
        cls.student = User.objects.create_user("student", password="pass")
        cls.other = User.objects.create_user("other", password="pass")
        cls.admin = User.objects.create_user("admin", password="pass", is_staff=True)
        cls.offer = Offer.objects.create(
            title="Practical logo design",
            description="Learn a repeatable process for creating clear and memorable logos.",
            category=category,
            level=Offer.Level.INTERMEDIATE,
            lesson_format=Offer.Format.ONLINE,
            duration_minutes=90,
            author=cls.mentor,
            status=Offer.Status.PUBLISHED,
        )

    def test_review_requires_completed_lesson(self):
        lesson_request = LessonRequest.objects.create(offer=self.offer, requester=self.student)
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("review_create", args=[lesson_request.pk]),
            {"rating": 5, "comment": "A very useful lesson."},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Review.objects.count(), 0)

    def test_only_requester_can_review_completed_lesson(self):
        lesson_request = LessonRequest.objects.create(
            offer=self.offer, requester=self.student, status=LessonRequest.Status.COMPLETED
        )
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("review_create", args=[lesson_request.pk]),
            {"rating": 5, "comment": "A very useful lesson."},
        )
        self.assertEqual(response.status_code, 403)

    def test_one_review_is_created_per_completed_lesson(self):
        lesson_request = LessonRequest.objects.create(
            offer=self.offer, requester=self.student, status=LessonRequest.Status.COMPLETED
        )
        self.client.force_login(self.student)
        url = reverse("review_create", args=[lesson_request.pk])
        self.client.post(url, {"rating": 5, "comment": "A very useful lesson."})
        second = self.client.post(url, {"rating": 4, "comment": "Trying a second review."})
        self.assertEqual(Review.objects.count(), 1)
        self.assertRedirects(second, reverse("review_update", args=[lesson_request.review.pk]))
        self.assertEqual(self.offer.average_rating, 5.0)

    def test_author_can_edit_and_admin_can_delete_review(self):
        lesson_request = LessonRequest.objects.create(
            offer=self.offer, requester=self.student, status=LessonRequest.Status.COMPLETED
        )
        review = Review.objects.create(
            lesson_request=lesson_request,
            offer=self.offer,
            author=self.student,
            rating=4,
            comment="Clear and practical lesson.",
        )
        self.client.force_login(self.student)
        self.client.post(
            reverse("review_update", args=[review.pk]),
            {"rating": 5, "comment": "Clear, practical, and friendly lesson."},
        )
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)

        self.client.force_login(self.admin)
        self.client.post(reverse("review_delete", args=[review.pk]))
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())

