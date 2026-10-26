from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if instance.is_superuser:
        role = Profile.Role.SUPER_ADMIN
    elif instance.is_staff:
        role = Profile.Role.ADMIN
    else:
        role = Profile.Role.USER

    Profile.objects.get_or_create(user=instance, defaults={"role": role})

