from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count, Q
from django.db.models.deletion import ProtectedError
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AdminOfferForm, CategoryForm, ModerationForm, OfferFilterForm, OfferForm
from .models import Category, Favorite, Offer


def _published_offers():
    return (
        Offer.objects.filter(status=Offer.Status.PUBLISHED, author__is_active=True)
        .select_related("author", "author__profile", "category")
        .annotate(
            rating_value=Avg("reviews__rating"),
            rating_total=Count("reviews", distinct=True),
            completed_total=Count(
                "lesson_requests",
                filter=Q(lesson_requests__status="completed"),
                distinct=True,
            ),
        )
    )


def _filter_offers(queryset, data):
    form = OfferFilterForm(data)
    if form.is_valid():
        q = form.cleaned_data.get("q")
        category = form.cleaned_data.get("category")
        level = form.cleaned_data.get("level")
        lesson_format = form.cleaned_data.get("lesson_format")
        min_rating = form.cleaned_data.get("min_rating")
        if q:
            queryset = queryset.filter(title__icontains=q.strip())
        if category:
            queryset = queryset.filter(category=category)
        if level:
            queryset = queryset.filter(level=level)
        if lesson_format:
            queryset = queryset.filter(lesson_format=lesson_format)
        if min_rating:
            queryset = queryset.filter(rating_value__gte=int(min_rating))
    return queryset, form


def explore(request):
    offers, filter_form = _filter_offers(_published_offers(), request.GET)
    return render(
        request,
        "offers/offer_list.html",
        {"offers": offers, "filter_form": filter_form, "page_title": "Explore skills"},
    )


def popular(request):
    offers, filter_form = _filter_offers(_published_offers().filter(rating_value__gte=4), request.GET)
    return render(
        request,
        "offers/offer_list.html",
        {"offers": offers, "filter_form": filter_form, "page_title": "Popular skills"},
    )


def category_list(request):
    categories = Category.objects.annotate(
        published_count=Count("offers", filter=Q(offers__status="published"))
    )
    return render(request, "offers/category_list.html", {"categories": categories})


def category_offers(request, slug):
    category = get_object_or_404(Category, slug=slug)
    offers, filter_form = _filter_offers(_published_offers().filter(category=category), request.GET)
    return render(
        request,
        "offers/offer_list.html",
        {"offers": offers, "filter_form": filter_form, "page_title": category.name},
    )


def offer_detail(request, pk):
    offer = get_object_or_404(
        Offer.objects.select_related("author", "author__profile", "category").prefetch_related(
            "reviews__author"
        ),
        pk=pk,
    )
    can_preview = request.user.is_authenticated and (
        request.user == offer.author or request.user.is_staff
    )
    if offer.status != Offer.Status.PUBLISHED and not can_preview:
        raise Http404
    is_favorite = request.user.is_authenticated and Favorite.objects.filter(
        user=request.user, offer=offer
    ).exists()
    active_request = None
    if request.user.is_authenticated:
        active_request = offer.lesson_requests.filter(
            requester=request.user, status__in=["pending", "accepted"]
        ).first()
    return render(
        request,
        "offers/offer_detail.html",
        {"offer": offer, "is_favorite": is_favorite, "active_request": active_request},
    )


def _user_can_create(user):
    return user.is_authenticated and user.is_active


@login_required
def offer_create(request):
    if not request.user.is_active:
        return HttpResponseForbidden("Banned users cannot create offers.")
    form = OfferForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        offer = form.save(commit=False)
        offer.author = request.user
        offer.status = (
            Offer.Status.DRAFT if "save_draft" in request.POST else Offer.Status.PENDING
        )
        offer.save()
        message = "Draft saved." if offer.status == Offer.Status.DRAFT else "Offer sent for moderation."
        messages.success(request, message)
        return redirect("my_offers")
    return render(request, "offers/offer_form.html", {"form": form, "page_title": "Create offer"})


@login_required
def offer_update(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    if request.user != offer.author and not request.user.is_staff:
        return HttpResponseForbidden("You cannot edit this offer.")
    form_class = AdminOfferForm if request.user.is_staff and request.user != offer.author else OfferForm
    form = form_class(request.POST or None, request.FILES or None, instance=offer)
    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        if form_class is OfferForm:
            updated.status = (
                Offer.Status.DRAFT if "save_draft" in request.POST else Offer.Status.PENDING
            )
            updated.rejection_reason = ""
        updated.save()
        messages.success(request, "Offer updated successfully.")
        return redirect("offer_detail", pk=offer.pk)
    return render(request, "offers/offer_form.html", {"form": form, "page_title": "Edit offer"})


@login_required
def offer_delete(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    if request.user != offer.author and not request.user.is_staff:
        return HttpResponseForbidden("You cannot delete this offer.")
    if request.method == "POST":
        offer.delete()
        messages.success(request, "Offer deleted.")
        return redirect("my_offers" if not request.user.is_staff else "offer_explore")
    return render(request, "offers/offer_confirm_delete.html", {"offer": offer})


@login_required
def my_offers(request):
    offers = request.user.offers.select_related("category")
    return render(request, "offers/my_offers.html", {"offers": offers})


@login_required
def toggle_favorite(request, pk):
    if request.method != "POST":
        return HttpResponseForbidden()
    offer = get_object_or_404(Offer, pk=pk, status=Offer.Status.PUBLISHED)
    favorite, created = Favorite.objects.get_or_create(user=request.user, offer=offer)
    if created:
        messages.success(request, "Added to favorites.")
    else:
        favorite.delete()
        messages.success(request, "Removed from favorites.")
    return redirect(request.POST.get("next") or "offer_detail", pk=offer.pk)


@login_required
def favorites(request):
    offers = _published_offers().filter(favorited_by__user=request.user)
    return render(request, "offers/favorites.html", {"offers": offers})


def staff_required(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(staff_required)
def moderation_queue(request):
    offers = Offer.objects.filter(status=Offer.Status.PENDING).select_related("author", "category")
    return render(request, "offers/moderation_queue.html", {"offers": offers})


@user_passes_test(staff_required)
def moderate_offer(request, pk):
    offer = get_object_or_404(Offer, pk=pk, status=Offer.Status.PENDING)
    form = ModerationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if form.cleaned_data["decision"] == "publish":
            offer.status = Offer.Status.PUBLISHED
            offer.rejection_reason = ""
            messages.success(request, "Offer published.")
        else:
            offer.status = Offer.Status.REJECTED
            offer.rejection_reason = form.cleaned_data["rejection_reason"].strip()
            messages.success(request, "Offer rejected.")
        offer.save(update_fields=["status", "rejection_reason", "updated_at"])
        return redirect("moderation_queue")
    return render(request, "offers/moderate_offer.html", {"offer": offer, "form": form})


@user_passes_test(lambda user: user.is_authenticated and user.is_superuser)
def category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category created.")
        return redirect("category_list")
    return render(request, "offers/category_form.html", {"form": form, "page_title": "Create category"})


@user_passes_test(lambda user: user.is_authenticated and user.is_superuser)
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category updated.")
        return redirect("category_list")
    return render(request, "offers/category_form.html", {"form": form, "page_title": "Edit category"})


@user_passes_test(lambda user: user.is_authenticated and user.is_superuser)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        try:
            category.delete()
            messages.success(request, "Category deleted.")
        except ProtectedError:
            messages.error(request, "A category used by offers cannot be deleted.")
        return redirect("category_list")
    return render(request, "offers/category_confirm_delete.html", {"category": category})

