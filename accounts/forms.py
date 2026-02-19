"""
Authentication forms with clean validation.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate

from .models import CustomUser


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "placeholder": "you@example.com"}),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
    )

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            user = authenticate(self.request, username=email, password=password)
            if user is None:
                raise ValidationError("Invalid email or password.")
            if not user.is_active:
                raise ValidationError("This account is inactive.")
            cleaned["user"] = user
        return cleaned

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)


class CollegeAdminRegistrationForm(forms.Form):
    """Registration for College Admin only. Creates College + User + CollegeAdmin profile."""
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "placeholder": "admin@college.edu"}),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm password"}),
    )
    first_name = forms.CharField(max_length=150, label="First name")
    last_name = forms.CharField(max_length=150, label="Last name")
    college_name = forms.CharField(max_length=255, label="College name")
    college_code = forms.CharField(
        max_length=50,
        label="College code",
        help_text="Unique short code (e.g. ABC)",
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_college_code(self):
        code = (self.cleaned_data.get("college_code") or "").strip().upper()
        if not code:
            raise ValidationError("College code is required.")
        from colleges.models import College
        if College.objects.filter(code__iexact=code).exists():
            raise ValidationError("A college with this code already exists.")
        return code

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Passwords do not match.")
        if p1 and len(p1) < 8:
            raise ValidationError("Password must be at least 8 characters.")
        return cleaned

    def save(self):
        from colleges.models import College, CollegeAdmin

        user = CustomUser.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            role=CustomUser.Role.COLLEGE_ADMIN,
        )
        college = College.objects.create(
            name=self.cleaned_data["college_name"],
            code=self.cleaned_data["college_code"],
        )
        CollegeAdmin.objects.create(user=user, college=college)
        return user
