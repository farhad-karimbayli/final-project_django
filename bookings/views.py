from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import is_banned
from offers.models import Offer

from .forms import LessonRequestForm
from .models import LessonRequest


@login_required
def send_request(request, offer_id):
    if request.method != "POST":
        return HttpResponseForbidden()
    offer = get_object_or_404(Offer, pk=offer_id, status=Offer.Status.PUBLISHED)
    if request.user == offer.author:
        messages.error(request, "You cannot request your own lesson.")
        return redirect("offer_detail", pk=offer.pk)
    if is_banned(request.user):
        return HttpResponseForbidden("Banned users cannot send lesson requests.")
    form = LessonRequestForm(request.POST)
    if form.is_valid():
        lesson_request = form.save(commit=False)
        lesson_request.offer = offer
        lesson_request.requester = request.user
        try:
            lesson_request.full_clean()
            lesson_request.save()
            messages.success(request, "Lesson request sent.")
        except (IntegrityError, ValidationError) as exc:
            if isinstance(exc, IntegrityError) or LessonRequest.objects.filter(
                offer=offer,
                requester=request.user,
                status__in=[LessonRequest.Status.PENDING, LessonRequest.Status.ACCEPTED],
            ).exists():
                messages.error(request, "You already have an active request for this offer.")
            else:
                messages.error(request, "The lesson request could not be sent.")
    else:
        messages.error(request, "Please correct the request message.")
    return redirect("offer_detail", pk=offer.pk)


@login_required
def my_requests(request):
    sent = LessonRequest.objects.filter(requester=request.user).select_related(
        "offer", "offer__author", "review"
    )
    received = LessonRequest.objects.filter(offer__author=request.user).select_related(
        "offer", "requester"
    )
    return render(request, "bookings/my_requests.html", {"sent": sent, "received": received})


@login_required
def update_request_status(request, pk, action):
    if request.method != "POST":
        return HttpResponseForbidden()
    lesson_request = get_object_or_404(
        LessonRequest.objects.select_related("offer", "requester"), pk=pk
    )
    owner_actions = {
        "accept": (LessonRequest.Status.PENDING, LessonRequest.Status.ACCEPTED),
        "reject": (LessonRequest.Status.PENDING, LessonRequest.Status.REJECTED),
        "complete": (LessonRequest.Status.ACCEPTED, LessonRequest.Status.COMPLETED),
    }
    if action in owner_actions:
        if request.user != lesson_request.offer.author:
            return HttpResponseForbidden("Only the offer owner can perform this action.")
        expected, target = owner_actions[action]
    elif action == "cancel":
        if request.user != lesson_request.requester:
            return HttpResponseForbidden("Only the requester can cancel this request.")
        expected = [LessonRequest.Status.PENDING, LessonRequest.Status.ACCEPTED]
        target = LessonRequest.Status.CANCELLED
    else:
        return HttpResponseForbidden("Unknown action.")

    allowed = lesson_request.status in expected if isinstance(expected, list) else lesson_request.status == expected
    if not allowed:
        messages.error(request, "This status change is not allowed.")
    else:
        lesson_request.status = target
        lesson_request.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Request marked as {lesson_request.get_status_display().lower()}.")
    return redirect("my_requests")

