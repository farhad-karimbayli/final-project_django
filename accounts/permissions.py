from .models import Profile


def get_profile(user):
    if not user.is_authenticated:
        return None
    return getattr(user, "profile", None)


def is_banned(user):
    profile = get_profile(user)
    return bool(profile and profile.is_banned)


def is_admin(user):
    profile = get_profile(user)
    return bool(profile and profile.is_admin)


def is_super_admin(user):
    profile = get_profile(user)
    return bool(profile and profile.is_super_admin)


def set_role(user, role):
    if role not in Profile.Role.values:
        raise ValueError("Unknown SkillSwap role.")

    profile = user.profile
    profile.role = role
    profile.save(update_fields=["role"])

    user.is_staff = role in {Profile.Role.ADMIN, Profile.Role.SUPER_ADMIN}
    user.is_superuser = role == Profile.Role.SUPER_ADMIN
    user.save(update_fields=["is_staff", "is_superuser"])
