"""Forms for creating and editing users in the admin."""

from django import forms
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from .models import User


class UserCreationForm(BaseUserCreationForm):
    """Used by the admin's 'add user' page."""

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ("email", "display_name")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email


class UserChangeForm(BaseUserChangeForm):
    """Used by the admin's 'edit user' page."""

    class Meta(BaseUserChangeForm.Meta):
        model = User
        fields = "__all__"