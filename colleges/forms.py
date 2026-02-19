from django import forms
from django.core.exceptions import ValidationError

from accounts.models import CustomUser


class TeacherRegistrationForm(forms.Form):
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True, "placeholder": "teacher@college.edu"}))
    password1 = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput(attrs={"placeholder": "Password"}))
    password2 = forms.CharField(label="Confirm password", strip=False, widget=forms.PasswordInput(attrs={"placeholder": "Confirm password"}))
    first_name = forms.CharField(max_length=150, label="First name")
    last_name = forms.CharField(max_length=150, label="Last name")
    employee_id = forms.CharField(max_length=50, label="Employee ID", required=False)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Passwords do not match.")
        if p1 and len(p1) < 8:
            raise ValidationError("Password must be at least 8 characters.")
        return cleaned

    def save(self, college):
        from colleges.models import Teacher

        user = CustomUser.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            role=CustomUser.Role.TEACHER,
        )
        Teacher.objects.create(user=user, college=college, employee_id=self.cleaned_data.get("employee_id") or None)
        return user


class StudentCSVUploadForm(forms.Form):
    title = forms.CharField(max_length=255, label="Batch Title", widget=forms.TextInput(attrs={"placeholder": "e.g., B.Tech 2nd Year 2024"}))
    description = forms.CharField(label="Description (optional)", required=False, widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Additional details about this student batch"}))
    csv_file = forms.FileField(label="CSV file", help_text="Required columns: name,email,dob. Optional: course")

    def clean_csv_file(self):
        file = self.cleaned_data.get("csv_file")
        if not file:
            return file
        import csv
        from io import TextIOWrapper

        if not file.name.lower().endswith(".csv"):
            raise ValidationError("File must be a CSV (.csv).")

        try:
            wrapper = TextIOWrapper(file.file, encoding="utf-8")
            reader = csv.DictReader(wrapper)
            rows = list(reader)
        except Exception as e:
            raise ValidationError(f"Could not read CSV: {str(e)}")

        if not rows:
            raise ValidationError("CSV is empty.")

        # Validate required columns
        required = {"name", "email", "dob"}
        cols = {c.strip() for c in reader.fieldnames or []}
        missing = required - cols
        if missing:
            raise ValidationError(f"Missing required columns: {', '.join(sorted(missing))}.")

        # Basic row validation
        validated = []
        errors = []
        from datetime import datetime

        for i, row in enumerate(rows):
            rnum = i + 2
            name = (row.get("name") or "").strip()
            email = (row.get("email") or "").strip()
            dob = (row.get("dob") or "").strip()
            course = (row.get("course") or "").strip() if row.get("course") is not None else None
            college_code = (row.get("college_code") or "").strip() if row.get("college_code") is not None else None

            if not name:
                errors.append(f"Row {rnum}: name is required.")
            if not email:
                errors.append(f"Row {rnum}: email is required.")
            try:
                dob_val = datetime.strptime(dob, "%Y-%m-%d").date()
            except Exception:
                errors.append(f"Row {rnum}: dob must be YYYY-MM-DD.")
                dob_val = None

            validated.append({"name": name, "email": email, "dob": dob_val, "course": course, "college_code": college_code})

        if errors:
            raise ValidationError(errors)

        self._validated_rows = validated
        file.seek(0)
        return file


class EditStudentForm(forms.ModelForm):
	class Meta:
		from colleges.models import Student
		model = Student
		fields = ["course", "date_of_birth"]
		widgets = {
			"date_of_birth": forms.DateInput(attrs={"type": "date"}),
		}
