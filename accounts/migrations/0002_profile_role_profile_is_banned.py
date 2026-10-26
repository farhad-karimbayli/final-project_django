from django.db import migrations, models


def migrate_existing_users(apps, schema_editor):
    Profile = apps.get_model("accounts", "Profile")
    User = apps.get_model("auth", "User")

    for profile in Profile.objects.select_related("user"):
        if profile.user.is_superuser:
            profile.role = "super_admin"
        elif profile.user.is_staff:
            profile.role = "admin"
        else:
            profile.role = "user"
        profile.is_banned = not profile.user.is_active
        profile.save(update_fields=["role", "is_banned"])

        if not profile.user.is_active:
            User.objects.filter(pk=profile.user_id).update(is_active=True)


def restore_django_flags(apps, schema_editor):
    Profile = apps.get_model("accounts", "Profile")
    User = apps.get_model("auth", "User")

    for profile in Profile.objects.all():
        User.objects.filter(pk=profile.user_id).update(
            is_active=not profile.is_banned,
            is_staff=profile.role in {"admin", "super_admin"},
            is_superuser=profile.role == "super_admin",
        )


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="is_banned",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="role",
            field=models.CharField(
                choices=[
                    ("user", "User"),
                    ("admin", "Admin"),
                    ("super_admin", "Super Admin"),
                ],
                default="user",
                max_length=20,
            ),
        ),
        migrations.RunPython(migrate_existing_users, restore_django_flags),
    ]
