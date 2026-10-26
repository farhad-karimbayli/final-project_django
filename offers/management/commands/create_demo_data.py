from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Profile
from accounts.permissions import set_role
from bookings.models import LessonRequest
from offers.management.commands.seed_categories import CATEGORY_NAMES
from offers.models import Category, Favorite, Offer
from reviews.models import Review


class Command(BaseCommand):
    help = "Create repeatable demo users, offers, requests, favorites, and reviews"

    def add_arguments(self, parser):
        parser.add_argument("--password", required=True, help="Password for all demo accounts")

    def handle(self, *args, **options):
        password = options["password"]
        if len(password) < 8:
            raise CommandError("The demo password must contain at least 8 characters.")

        categories = {}
        for name in CATEGORY_NAMES:
            categories[name], _ = Category.objects.get_or_create(
                name=name, defaults={"slug": name.lower().replace(" ", "-")}
            )

        mentor, _ = User.objects.get_or_create(
            username="demo_mentor", defaults={"email": "mentor@example.com"}
        )
        student, _ = User.objects.get_or_create(
            username="demo_student", defaults={"email": "student@example.com"}
        )
        admin, _ = User.objects.get_or_create(
            username="demo_admin", defaults={"email": "admin@example.com"}
        )
        for account in (mentor, student, admin):
            account.is_active = True
            account.set_password(password)
            account.save()

        set_role(mentor, Profile.Role.USER)
        set_role(student, Profile.Role.USER)
        set_role(admin, Profile.Role.ADMIN)
        mentor.profile.is_banned = False
        student.profile.is_banned = False
        admin.profile.is_banned = False
        Profile.objects.bulk_update(
            [mentor.profile, student.profile, admin.profile], ["is_banned"]
        )

        mentor.profile.bio = "Python developer who enjoys helping beginners build real projects."
        mentor.profile.save()
        student.profile.bio = "Curious learner interested in programming and design."
        student.profile.save()

        offer, _ = Offer.objects.update_or_create(
            author=mentor,
            title="Build your first Django website",
            defaults={
                "description": "A friendly practical lesson covering URLs, views, templates, models, and forms.",
                "category": categories["Programming"],
                "level": Offer.Level.BEGINNER,
                "lesson_format": Offer.Format.ONLINE,
                "duration_minutes": 75,
                "status": Offer.Status.PUBLISHED,
                "rejection_reason": "",
            },
        )
        Offer.objects.update_or_create(
            author=mentor,
            title="Python problem-solving practice",
            defaults={
                "description": "Solve practical Python exercises and learn how to explain each solution clearly.",
                "category": categories["Programming"],
                "level": Offer.Level.INTERMEDIATE,
                "lesson_format": Offer.Format.OFFLINE,
                "duration_minutes": 60,
                "status": Offer.Status.PUBLISHED,
                "rejection_reason": "",
            },
        )
        lesson_request, _ = LessonRequest.objects.update_or_create(
            offer=offer,
            requester=student,
            defaults={
                "message": "I want to understand how a complete Django project is structured.",
                "status": LessonRequest.Status.COMPLETED,
            },
        )
        Review.objects.update_or_create(
            lesson_request=lesson_request,
            defaults={
                "offer": offer,
                "author": student,
                "rating": 5,
                "comment": "Clear explanations and a very practical lesson.",
            },
        )
        Favorite.objects.get_or_create(user=student, offer=offer)
        self.stdout.write(
            self.style.SUCCESS("Demo data is ready: demo_mentor, demo_student, and demo_admin.")
        )

