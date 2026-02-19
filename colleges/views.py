from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .forms import TeacherRegistrationForm
from accounts.models import CustomUser


# College management views


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def register_teacher_view(request):
	# Only college admins may create teachers
	if not hasattr(request.user, "college_admin_profile") or request.user.role != CustomUser.Role.COLLEGE_ADMIN:
		messages.error(request, "Access denied.")
		return redirect("accounts:dashboard")
	college = request.user.college_admin_profile.college
	if request.method == "POST":
		form = TeacherRegistrationForm(data=request.POST)
		if form.is_valid():
			form.save(college=college)
			messages.success(request, "Teacher registered successfully.")
			return redirect("accounts:dashboard_college_admin")
		messages.error(request, "Please correct the errors below.")
	else:
		form = TeacherRegistrationForm()
	return render(request, "colleges/register_teacher.html", {"form": form, "college": college})


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def import_students_view(request):
	if not hasattr(request.user, "college_admin_profile") or request.user.role != CustomUser.Role.COLLEGE_ADMIN:
		messages.error(request, "Access denied.")
		return redirect("accounts:dashboard")
	college = request.user.college_admin_profile.college
	if request.method == "POST":
		from .forms import StudentCSVUploadForm
		csv_form = StudentCSVUploadForm(data=request.POST, files=request.FILES)
		if csv_form.is_valid():
			rows = csv_form._validated_rows
			title = csv_form.cleaned_data.get("title", "").strip()
			description = csv_form.cleaned_data.get("description", "").strip()
			import uuid
			from django.db import transaction
			from colleges.models import Student, StudentBatch
			created = 0
			try:
				with transaction.atomic():
					# Create batch
					batch = StudentBatch.objects.create(college=college, title=title, description=description)
					for i, r in enumerate(rows):
						name = r["name"].strip()
						email = r["email"].strip()
						dob = r["dob"]
						course = r.get("course")

						if CustomUser.objects.filter(email__iexact=email).exists():
							raise ValueError(f"Row {i+2}: User with email {email} already exists.")

						# Create user
						user = CustomUser.objects.create_user(
							email=email,
							password=uuid.uuid4().hex[:10],
							first_name=name.split()[0] if name else "",
							last_name=" ".join(name.split()[1:]) if len(name.split()) > 1 else "",
							role=CustomUser.Role.STUDENT,
						)

						# Generate unique student_id
						from uuid import uuid4
						for _ in range(5):
							candidate = f"{college.code}-{uuid4().hex[:8].upper()}"
							if not Student.objects.filter(college=college, student_id__iexact=candidate).exists():
								student_id = candidate
								break
						else:
							raise ValueError(f"Could not generate unique student ID for row {i+2}.")

						Student.objects.create(user=user, college=college, batch=batch, student_id=student_id, date_of_birth=dob, course=course)
						created += 1
				messages.success(request, f"Imported {created} student(s) in batch '{title}'.")
				return redirect("colleges:manage_students")
			except Exception as e:
				messages.error(request, f"Import failed: {str(e)}")
		else:
			for field, errs in csv_form.errors.items():
				for err in errs:
					messages.error(request, f"{field}: {err}")
	else:
		csv_form = None
	return render(request, "colleges/import_students.html", {"form": csv_form, "college": college})


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def manage_students_view(request):
	if not hasattr(request.user, "college_admin_profile") or request.user.role != CustomUser.Role.COLLEGE_ADMIN:
		messages.error(request, "Access denied.")
		return redirect("accounts:dashboard")
	college = request.user.college_admin_profile.college

	# Handle delete student
	if request.method == "POST" and request.POST.get("action") == "delete":
		student_id = request.POST.get("student_id")
		try:
			from colleges.models import Student
			student = Student.objects.get(pk=student_id, college=college)
			user = student.user
			student.delete()
			user.delete()
			messages.success(request, f"Student deleted successfully.")
		except Student.DoesNotExist:
			messages.error(request, "Student not found.")
		except Exception as e:
			messages.error(request, f"Could not delete: {str(e)}")
		return redirect("colleges:manage_students")

	# Get batches and students grouped by batch
	from colleges.models import StudentBatch
	batches = college.student_batches.prefetch_related("students__user").all()
	
	context = {
		"college": college,
		"batches": batches,
	}
	return render(request, "colleges/manage_students.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def edit_student_view(request, student_id):
	if not hasattr(request.user, "college_admin_profile") or request.user.role != CustomUser.Role.COLLEGE_ADMIN:
		messages.error(request, "Access denied.")
		return redirect("accounts:dashboard")
	college = request.user.college_admin_profile.college
	
	from colleges.models import Student
	try:
		student = Student.objects.get(pk=student_id, college=college)
	except Student.DoesNotExist:
		messages.error(request, "Student not found.")
		return redirect("colleges:manage_students")

	if request.method == "POST":
		from .forms import EditStudentForm
		form = EditStudentForm(data=request.POST, instance=student)
		if form.is_valid():
			form.save()
			messages.success(request, "Student updated successfully.")
			return redirect("colleges:manage_students")
	else:
		from .forms import EditStudentForm
		form = EditStudentForm(instance=student)

	return render(request, "colleges/edit_student.html", {"form": form, "student": student, "college": college})
