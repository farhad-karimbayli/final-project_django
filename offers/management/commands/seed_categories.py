from django.core.management.base import BaseCommand
from django.utils.text import slugify

from offers.models import Category


CATEGORY_NAMES = [
    "Programming",
    "Design",
    "Languages",
    "Marketing",
    "Music",
    "Photography",
    "Business",
    "Mathematics",
    "Other",
]


class Command(BaseCommand):
    help = "Create the default SkillSwap categories"

    def handle(self, *args, **options):
        created_count = 0
        for name in CATEGORY_NAMES:
            _, created = Category.objects.get_or_create(name=name, defaults={"slug": slugify(name)})
            created_count += int(created)
        self.stdout.write(self.style.SUCCESS(f"Categories ready. Created: {created_count}."))

