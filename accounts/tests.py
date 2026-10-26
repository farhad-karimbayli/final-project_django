from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile


class AccountTests(TestCase):
    def test_registration_creates_profile_and_logs_user_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "learner",
                "email": "learner@example.com",
                "password1": "StrongPass2026!",
                "password2": "StrongPass2026!",
            },
        )
        user = User.objects.get(username="learner")
        self.assertRedirects(response, reverse("profile_edit"))
        self.assertEqual(user.profile.bio, "")
        self.assertEqual(user.profile.role, Profile.Role.USER)
        self.assertFalse(user.profile.is_banned)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user("first", "person@example.com", "StrongPass2026!")
        response = self.client.post(
            reverse("register"),
            {
                "username": "second",
                "email": "PERSON@example.com",
                "password1": "StrongPass2026!",
                "password2": "StrongPass2026!",
            },
        )
        self.assertContains(response, "already exists")
        self.assertFalse(User.objects.filter(username="second").exists())

    def test_admin_can_ban_user_but_cannot_ban_superuser(self):
        admin = User.objects.create_user("admin", password="pass", is_staff=True)
        member = User.objects.create_user("member", password="pass")
        root = User.objects.create_superuser("root", "root@example.com", "pass")
        self.client.force_login(admin)

        self.client.post(reverse("toggle_ban", args=[member.pk]))
        member.profile.refresh_from_db()
        self.assertTrue(member.profile.is_banned)
        self.assertTrue(member.is_active)

        self.client.post(reverse("toggle_ban", args=[root.pk]))
        root.profile.refresh_from_db()
        self.assertFalse(root.profile.is_banned)

    def test_only_superuser_can_assign_admin(self):
        admin = User.objects.create_user("admin", password="pass", is_staff=True)
        member = User.objects.create_user("member", password="pass")
        self.client.force_login(admin)
        response = self.client.post(reverse("toggle_admin", args=[member.pk]))
        self.assertEqual(response.status_code, 302)
        member.profile.refresh_from_db()
        self.assertEqual(member.profile.role, Profile.Role.USER)

        root = User.objects.create_superuser("root", "root@example.com", "pass")
        self.assertEqual(root.profile.role, Profile.Role.SUPER_ADMIN)
        self.client.force_login(root)
        self.client.post(reverse("toggle_admin", args=[member.pk]))
        member.refresh_from_db()
        member.profile.refresh_from_db()
        self.assertTrue(member.is_staff)
        self.assertEqual(member.profile.role, Profile.Role.ADMIN)

    def test_banned_user_can_log_in(self):
        blocked = User.objects.create_user("blocked", password="StrongPass2026!")
        blocked.profile.is_banned = True
        blocked.profile.save(update_fields=["is_banned"])
        self.assertTrue(self.client.login(username="blocked", password="StrongPass2026!"))

    def test_admin_permissions_use_profile_role_not_is_staff(self):
        admin = User.objects.create_user("role_admin", password="pass")
        admin.profile.role = Profile.Role.ADMIN
        admin.profile.save(update_fields=["role"])
        self.assertFalse(admin.is_staff)

        self.client.force_login(admin)
        response = self.client.get(reverse("user_management"))
        self.assertEqual(response.status_code, 200)

