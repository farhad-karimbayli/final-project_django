from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from offers.models import Category, Offer

from .models import LessonRequest


class LessonRequestTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.get(name="Music")
        cls.mentor = User.objects.create_user("mentor", password="pass")
        cls.student = User.objects.create_user("student", password="pass")
        cls.other = User.objects.create_user("other", password="pass")
        cls.offer = Offer.objects.create(
            title="Acoustic guitar lessons",
            description="Learn chords, rhythm, and complete songs with guided practice.",
            category=category,
            level=Offer.Level.BEGINNER,
            lesson_format=Offer.Format.OFFLINE,
            duration_minutes=60,
            author=cls.mentor,
            status=Offer.Status.PUBLISHED,
        )

    def test_user_cannot_request_own_offer(self):
        self.client.force_login(self.mentor)
        self.client.post(reverse("send_request", args=[self.offer.pk]), {"message": ""})
        self.assertEqual(LessonRequest.objects.count(), 0)

    def test_duplicate_active_request_is_prevented(self):
        self.client.force_login(self.student)
        url = reverse("send_request", args=[self.offer.pk])
        self.client.post(url, {"message": "I would like a weekend lesson."})
        self.client.post(url, {"message": "Sending the same request again."})
        self.assertEqual(LessonRequest.objects.count(), 1)

    def test_offer_owner_controls_accept_reject_and_complete(self):
        lesson_request = LessonRequest.objects.create(offer=self.offer, requester=self.student)
        self.client.force_login(self.other)
        forbidden = self.client.post(
            reverse("update_request_status", args=[lesson_request.pk, "accept"])
        )
        self.assertEqual(forbidden.status_code, 403)

        self.client.force_login(self.mentor)
        self.client.post(reverse("update_request_status", args=[lesson_request.pk, "accept"]))
        lesson_request.refresh_from_db()
        self.assertEqual(lesson_request.status, LessonRequest.Status.ACCEPTED)
        self.client.post(reverse("update_request_status", args=[lesson_request.pk, "complete"]))
        lesson_request.refresh_from_db()
        self.assertEqual(lesson_request.status, LessonRequest.Status.COMPLETED)

    def test_requester_can_cancel_active_request(self):
        lesson_request = LessonRequest.objects.create(offer=self.offer, requester=self.student)
        self.client.force_login(self.student)
        self.client.post(reverse("update_request_status", args=[lesson_request.pk, "cancel"]))
        lesson_request.refresh_from_db()
        self.assertEqual(lesson_request.status, LessonRequest.Status.CANCELLED)

