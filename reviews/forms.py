from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "rating": forms.Select(choices=[(number, f"{number} / 5") for number in range(1, 6)]),
            "comment": forms.Textarea(attrs={"rows": 5}),
        }

    def clean_comment(self):
        comment = self.cleaned_data["comment"].strip()
        if len(comment) < 10:
            raise forms.ValidationError("The review must contain at least 10 characters.")
        return comment

