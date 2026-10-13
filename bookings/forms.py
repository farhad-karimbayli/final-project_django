from django import forms

from .models import LessonRequest


class LessonRequestForm(forms.ModelForm):
    class Meta:
        model = LessonRequest
        fields = ("message",)
        widgets = {
            "message": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Introduce yourself and suggest a suitable time."}
            )
        }

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if message and len(message) < 10:
            raise forms.ValidationError("Please write at least 10 characters or leave it blank.")
        return message

