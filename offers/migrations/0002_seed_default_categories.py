from django.db import migrations
from django.utils.text import slugify


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


def seed_categories(apps, schema_editor):
    Category = apps.get_model("offers", "Category")
    for name in CATEGORY_NAMES:
        Category.objects.get_or_create(name=name, defaults={"slug": slugify(name)})


def remove_categories(apps, schema_editor):
    Category = apps.get_model("offers", "Category")
    Category.objects.filter(name__in=CATEGORY_NAMES, offers__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("offers", "0001_initial")]
    operations = [migrations.RunPython(seed_categories, remove_categories)]

