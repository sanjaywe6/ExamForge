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
        required=False,
        widget=forms.EmailInput(attrs={"autofocus": True, "placeholder": "you@example.com"}),
    )
    password = forms.CharField(
        label="Password",
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
    )
    account_type = forms.ChoiceField(
        label="Login as",
        choices=(('staff', 'College / Teacher'), ('student', 'Student')),
        widget=forms.RadioSelect,
        initial='staff',
    )
    # Student quick-login fields
    college_code = forms.CharField(max_length=50, required=False, label="College code", widget=forms.TextInput(attrs={"placeholder": "e.g. ABC"}))
    student_id = forms.CharField(max_length=50, required=False, label="Student ID", widget=forms.TextInput(attrs={"placeholder": "Your student ID"}))
    student_email = forms.EmailField(required=False, label="Student email", widget=forms.EmailInput(attrs={"placeholder": "student@example.com"}))

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        atype = cleaned.get("account_type")
        if atype == 'student':
            # Validate student quick-login fields (college code + student id + student email)
            code = (cleaned.get("college_code") or "").strip().upper()
            sid = (cleaned.get("student_id") or "").strip()
            semail = (cleaned.get("student_email") or "").strip()
            if not (code and sid and semail):
                raise ValidationError("College code, Student ID and Student email are required for Student login.")
            from colleges.models import College, Student as StudentModel
            college = College.objects.filter(code__iexact=code).first()
            if not college:
                raise ValidationError("College code not found.")
            student = StudentModel.objects.filter(college=college, student_id__iexact=sid).select_related("user").first()
            if not student:
                raise ValidationError("Student not found.")
            if (student.user.email or "").strip().lower() != semail.lower():
                raise ValidationError("Student email does not match our records.")
            user = student.user
            if not user.is_active:
                raise ValidationError("This account is inactive.")
            cleaned["user"] = user
        else:
            # Staff login uses email/password
            if not email or not password:
                raise ValidationError("Email and password are required for staff login.")
            user = authenticate(self.request, username=email, password=password)
            if user is None:
                raise ValidationError("Invalid email or password.")
            if not user.is_active:
                raise ValidationError("This account is inactive.")
            # Prevent staff using student-only login
            if user.role == CustomUser.Role.STUDENT:
                raise ValidationError("Please use the Student login option for student accounts.")
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


class ProfileEditForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False, label="First name")
    last_name = forms.CharField(max_length=150, required=False, label="Last name")
    email = forms.EmailField(label="Email")

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        initial = kwargs.get('initial', {})
        if user is not None:
            initial.setdefault('first_name', user.first_name)
            initial.setdefault('last_name', user.last_name)
            initial.setdefault('email', user.email)
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.exclude(pk=getattr(self.user, 'pk', None)).filter(email__iexact=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email

    def save(self):
        if not self.user:
            raise RuntimeError('ProfileEditForm requires a `user` instance to save.')
        self.user.first_name = self.cleaned_data.get('first_name') or ''
        self.user.last_name = self.cleaned_data.get('last_name') or ''
        self.user.email = self.cleaned_data.get('email')
        self.user.save()
        return self.user
