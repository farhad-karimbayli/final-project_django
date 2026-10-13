from django import forms

from .models import Category, Offer


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = (
            "title",
            "description",
            "image",
            "category",
            "level",
            "lesson_format",
            "duration_minutes",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "duration_minutes": forms.NumberInput(attrs={"min": 15, "step": 5}),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 5:
            raise forms.ValidationError("The title must contain at least 5 characters.")
        return title

    def clean_description(self):
        description = self.cleaned_data["description"].strip()
        if len(description) < 30:
            raise forms.ValidationError("The description must contain at least 30 characters.")
        return description


class AdminOfferForm(OfferForm):
    class Meta(OfferForm.Meta):
        fields = OfferForm.Meta.fields + ("status", "rejection_reason")


class OfferFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": "Search by title"}),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), required=False, empty_label="All categories"
    )
    level = forms.ChoiceField(
        choices=[("", "All levels"), *Offer.Level.choices], required=False
    )
    lesson_format = forms.ChoiceField(
        choices=[("", "All formats"), *Offer.Format.choices], required=False, label="Format"
    )
    min_rating = forms.ChoiceField(
        choices=[("", "Any rating"), ("1", "1+"), ("2", "2+"), ("3", "3+"), ("4", "4+")],
        required=False,
        label="Minimum rating",
    )


class ModerationForm(forms.Form):
    decision = forms.ChoiceField(choices=(("publish", "Publish"), ("reject", "Reject")))
    rejection_reason = forms.CharField(
        required=False, max_length=500, widget=forms.Textarea(attrs={"rows": 3})
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("decision") == "reject" and not cleaned.get("rejection_reason", "").strip():
            self.add_error("rejection_reason", "Please explain why the offer was rejected.")
        return cleaned


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "slug")

