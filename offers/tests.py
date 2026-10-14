from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Category, Favorite, Offer


class OfferTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.get(name="Programming")
        cls.owner = User.objects.create_user("mentor", password="pass")
        cls.other = User.objects.create_user("student", password="pass")
        cls.admin = User.objects.create_user("admin", password="pass", is_staff=True)
        cls.offer = Offer.objects.create(
            title="Learn Python basics",
            description="A practical introduction to Python for complete beginners.",
            category=cls.category,
            level=Offer.Level.BEGINNER,
            lesson_format=Offer.Format.ONLINE,
            duration_minutes=60,
            author=cls.owner,
            status=Offer.Status.PUBLISHED,
        )

    def offer_data(self, **changes):
        data = {
            "title": "Build useful Django apps",
            "description": "Learn how to build a complete Django application step by step.",
            "category": self.category.pk,
            "level": Offer.Level.INTERMEDIATE,
            "lesson_format": Offer.Format.ONLINE,
            "duration_minutes": 75,
        }
        data.update(changes)
        return data

    def test_guest_sees_only_published_offers(self):
        Offer.objects.create(
            **{key: value for key, value in self.offer_data(title="Hidden draft lesson").items() if key != "category"},
            category=self.category,
            author=self.owner,
            status=Offer.Status.DRAFT,
        )
        response = self.client.get(reverse("offer_explore"))
        self.assertContains(response, self.offer.title)
        self.assertNotContains(response, "Hidden draft lesson")

    def test_user_can_create_draft_or_pending_offer(self):
        self.client.force_login(self.other)
        self.client.post(reverse("offer_create"), {**self.offer_data(), "save_draft": "1"})
        self.assertTrue(Offer.objects.filter(author=self.other, status=Offer.Status.DRAFT).exists())

        self.client.post(reverse("offer_create"), self.offer_data(title="Understand data structures"))
        self.assertTrue(Offer.objects.filter(author=self.other, status=Offer.Status.PENDING).exists())

    def test_editing_published_offer_returns_it_to_moderation(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("offer_update", args=[self.offer.pk]), self.offer_data())
        self.offer.refresh_from_db()
        self.assertRedirects(response, reverse("offer_detail", args=[self.offer.pk]))
        self.assertEqual(self.offer.status, Offer.Status.PENDING)

    def test_user_cannot_edit_or_delete_another_users_offer(self):
        self.client.force_login(self.other)
        edit = self.client.post(reverse("offer_update", args=[self.offer.pk]), self.offer_data())
        delete = self.client.post(reverse("offer_delete", args=[self.offer.pk]))
        self.assertEqual(edit.status_code, 403)
        self.assertEqual(delete.status_code, 403)
        self.assertTrue(Offer.objects.filter(pk=self.offer.pk).exists())

    def test_admin_can_publish_pending_offer(self):
        self.offer.status = Offer.Status.PENDING
        self.offer.save()
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("moderate_offer", args=[self.offer.pk]),
            {"decision": "publish", "rejection_reason": ""},
        )
        self.offer.refresh_from_db()
        self.assertRedirects(response, reverse("moderation_queue"))
        self.assertEqual(self.offer.status, Offer.Status.PUBLISHED)

    def test_rejection_requires_a_reason(self):
        self.offer.status = Offer.Status.PENDING
        self.offer.save()
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("moderate_offer", args=[self.offer.pk]),
            {"decision": "reject", "rejection_reason": ""},
        )
        self.offer.refresh_from_db()
        self.assertContains(response, "Please explain")
        self.assertEqual(self.offer.status, Offer.Status.PENDING)

    def test_favorite_toggle_adds_and_removes_offer(self):
        self.client.force_login(self.other)
        url = reverse("toggle_favorite", args=[self.offer.pk])
        self.client.post(url)
        self.assertTrue(Favorite.objects.filter(user=self.other, offer=self.offer).exists())
        self.client.post(url)
        self.assertFalse(Favorite.objects.filter(user=self.other, offer=self.offer).exists())

    def test_search_and_filters_can_be_combined(self):
        response = self.client.get(
            reverse("offer_explore"),
            {"q": "python", "category": self.category.pk, "level": "beginner", "lesson_format": "online"},
        )
        self.assertContains(response, self.offer.title)
        response = self.client.get(reverse("offer_explore"), {"level": "advanced"})
        self.assertNotContains(response, self.offer.title)

    def test_demo_data_command_is_repeatable(self):
        call_command("create_demo_data", password="ExampleTest2026!", verbosity=0)
        call_command("create_demo_data", password="ExampleTest2026!", verbosity=0)
        self.assertEqual(User.objects.filter(username__startswith="demo_").count(), 3)
        self.assertEqual(Offer.objects.filter(author__username="demo_mentor").count(), 2)

