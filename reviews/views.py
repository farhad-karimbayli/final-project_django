from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import is_admin
from bookings.models import LessonRequest

from .forms import ReviewForm
from .models import Review


@login_required
def review_create(request, request_id):
    lesson_request = get_object_or_404(
        LessonRequest.objects.select_related("offer", "requester"), pk=request_id
    )
    if lesson_request.requester != request.user:
        return HttpResponseForbidden("Only the lesson requester can write a review.")
    if lesson_request.status != LessonRequest.Status.COMPLETED:
        return HttpResponseForbidden("The lesson must be completed first.")
    if hasattr(lesson_request, "review"):
        return redirect("review_update", pk=lesson_request.review.pk)
    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)
        review.lesson_request = lesson_request
        review.offer = lesson_request.offer
        review.author = request.user
        review.full_clean()
        review.save()
        messages.success(request, "Thank you for your review.")
        return redirect("offer_detail", pk=lesson_request.offer_id)
    return render(request, "reviews/review_form.html", {"form": form, "lesson_request": lesson_request})


@login_required
def review_update(request, pk):
    review = get_object_or_404(Review.objects.select_related("offer"), pk=pk)
    if review.author != request.user:
        return HttpResponseForbidden("You cannot edit this review.")
    form = ReviewForm(request.POST or None, instance=review)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Review updated.")
        return redirect("offer_detail", pk=review.offer_id)
    return render(request, "reviews/review_form.html", {"form": form, "lesson_request": review.lesson_request})


@login_required
def review_delete(request, pk):
    review = get_object_or_404(Review.objects.select_related("offer"), pk=pk)
    if review.author != request.user and not is_admin(request.user):
        return HttpResponseForbidden("You cannot delete this review.")
    if request.method == "POST":
        offer_id = review.offer_id
        review.delete()
        messages.success(request, "Review deleted.")
        return redirect("offer_detail", pk=offer_id)
    return render(request, "reviews/review_confirm_delete.html", {"review": review})

