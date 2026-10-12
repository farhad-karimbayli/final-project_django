from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProfileForm, RegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect("offer_explore")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome to SkillSwap!")
        return redirect("profile_edit")
    return render(request, "registration/register.html", {"form": form})


def profile_detail(request, username):
    user = get_object_or_404(
        User.objects.select_related("profile").prefetch_related(
            "offers__category", "offers__reviews"
        ),
        username=username,
    )
    published_offers = user.offers.filter(status="published").select_related("category")
    from reviews.models import Review

    reviews = Review.objects.filter(offer__author=user).select_related("author", "offer")
    return render(
        request,
        "accounts/profile_detail.html",
        {"profile_user": user, "published_offers": published_offers, "reviews": reviews},
    )


@login_required
def profile_edit(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user.profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("profile_detail", username=request.user.username)
    return render(request, "accounts/profile_form.html", {"form": form})


def mentor_list(request):
    mentors = (
        User.objects.filter(offers__status="published", is_active=True)
        .select_related("profile")
        .annotate(
            published_count=Count(
                "offers", filter=Q(offers__status="published"), distinct=True
            ),
            mentor_rating=Avg("offers__reviews__rating"),
        )
        .distinct()
        .order_by("username")
    )
    return render(request, "accounts/mentor_list.html", {"mentors": mentors})


def staff_required(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(staff_required)
def user_management(request):
    users = User.objects.select_related("profile").order_by("username")
    return render(request, "accounts/user_management.html", {"users": users})


@user_passes_test(staff_required)
def toggle_ban(request, user_id):
    if request.method != "POST":
        return HttpResponseForbidden()
    target = get_object_or_404(User, pk=user_id)
    if target == request.user or (target.is_superuser and not request.user.is_superuser):
        messages.error(request, "You cannot change this user's status.")
    else:
        target.is_active = not target.is_active
        target.save(update_fields=["is_active"])
        state = "unbanned" if target.is_active else "banned"
        messages.success(request, f"{target.username} has been {state}.")
    return redirect("user_management")


@user_passes_test(lambda user: user.is_authenticated and user.is_superuser)
def toggle_admin(request, user_id):
    if request.method != "POST":
        return HttpResponseForbidden()
    target = get_object_or_404(User, pk=user_id)
    if target.is_superuser:
        messages.error(request, "The super admin role cannot be changed here.")
    else:
        target.is_staff = not target.is_staff
        target.save(update_fields=["is_staff"])
        role = "admin" if target.is_staff else "user"
        messages.success(request, f"{target.username} is now an {role}.")
    return redirect("user_management")

