# Examination Portal — Database Schema Design

## Overview

This document describes the complete database schema for the Django Examination Portal. The design follows normalization principles, Django best practices, and enforces constraints at the database level.

---

## 1. Entity Relationship Overview

```
                    ┌─────────────┐
                    │  CustomUser │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌────────────┐  ┌──────────┐  ┌─────────────┐
    │ CollegeAdmin│  │ Teacher  │  │   Student   │
    └──────┬─────┘  └────┬─────┘  └──────┬──────┘
           │             │               │
           └─────────────┼───────────────┘
                         │
                    ┌────▼────┐
                    │ College │
                    └─────────┘
                         
    Teacher ──────► Exam ◄───── Question
                         │
                         │
    Student ──────► StudentAttempt ◄──── StudentAnswer
                         │                    │
                         │                    │
                         └────────────────────┘
                              (via Question)
```

---

## 2. Models with Explanations

### 2.1 CustomUser

**Why it exists:** Provides authentication and role-based access. Uses email as the primary identifier instead of username (required for custom User).

| Field        | Type     | Notes                                      |
|--------------|----------|--------------------------------------------|
| email        | EmailField | Unique, `USERNAME_FIELD`                  |
| role         | CharField | Choices: CollegeAdmin, Teacher, Student   |
| first_name   | CharField |                                            |
| last_name    | CharField |                                            |
| password     | CharField | Inherited from AbstractUser              |

**Indexes:** `role` (for filtering users by role)

---

### 2.2 College

**Why it exists:** Central entity for institutions. Teachers, Students, and CollegeAdmins are associated with a college.

| Field     | Type      | Notes              |
|-----------|-----------|--------------------|
| name      | CharField |                    |
| code      | CharField | Unique, indexed    |
| address   | TextField | Optional            |
| created_at| DateTime  | Auto                |

**Indexes:** `code` (unique, for lookups by college code)

---

### 2.3 Teacher

**Why it exists:** Links a User (with role=Teacher) to a College. Teachers create exams.

| Field       | Type       | Notes                               |
|-------------|------------|-------------------------------------|
| user        | OneToOne   | FK → CustomUser (role=TEACHER)      |
| college     | ForeignKey | FK → College                        |
| employee_id | CharField  | Optional, unique per college        |
| created_at  | DateTime   | Auto                                |

**Constraints:** `UniqueConstraint(college, employee_id)` where `employee_id` is non-empty — ensures unique employee IDs within a college.

**Indexes:** `college`, `employee_id`

---

### 2.4 Student

**Why it exists:** Links a User (with role=Student) to a College. Students attempt exams.

| Field      | Type       | Notes                               |
|------------|------------|-------------------------------------|
| user       | OneToOne   | FK → CustomUser (role=STUDENT)      |
| college    | ForeignKey | FK → College                        |
| roll_number| CharField  | Optional, unique per college        |
| created_at | DateTime   | Auto                                |

**Constraints:** `UniqueConstraint(college, roll_number)` where `roll_number` is non-empty.

**Indexes:** `college`, `roll_number`

---

### 2.5 CollegeAdmin

**Why it exists:** Links a User (with role=CollegeAdmin) to a College. Manages college-level operations (e.g., result publishing).

| Field      | Type       | Notes                                |
|------------|------------|--------------------------------------|
| user       | OneToOne   | FK → CustomUser (role=COLLEGE_ADMIN) |
| college    | ForeignKey | FK → College                         |
| created_at | DateTime   | Auto                                 |

**Indexes:** `college`

---

### 2.6 Exam

**Why it exists:** Represents a test/series created by a Teacher. Holds timing, marking, and result-publishing control.

| Field             | Type       | Notes                                  |
|-------------------|------------|----------------------------------------|
| created_by        | ForeignKey | FK → Teacher                           |
| title             | CharField  |                                        |
| description       | TextField  | Optional                                |
| test_code         | CharField  | Unique, auto-generated 8-char, indexed |
| start_time        | DateTime   |                                        |
| end_time          | DateTime   |                                        |
| duration_minutes  | PositiveInt| Must be ≥ 1                            |
| positive_marking  | Decimal    | Default 1, ≥ 0                         |
| negative_marking  | Decimal    | ≤ 0 (e.g., -0.25)                      |
| result_published  | Boolean    | Result publishing control              |
| created_at        | DateTime   | Auto                                   |
| updated_at        | DateTime   | Auto                                   |

**Constraints:**
- `CheckConstraint`: `end_time > start_time`
- `CheckConstraint`: `negative_marking <= 0`

**Indexes:** `test_code` (unique), `(start_time, end_time)`, `created_by`, `result_published`

**Normalization:** College is *not* stored on Exam — it is derived via `exam.created_by.college`.

---

### 2.7 Question

**Why it exists:** Belongs to an Exam. Stores question text, MCQ options (JSON), correct answer, and marks.

| Field          | Type       | Notes                                 |
|----------------|------------|---------------------------------------|
| exam           | ForeignKey | FK → Exam                             |
| order          | PositiveInt| Display order                         |
| question_text  | TextField  |                                       |
| options        | JSONField  | e.g. `{"A": "Option A", "B": "Option B"}` |
| correct_answer | CharField  | Key from options (e.g., "A")          |
| marks          | Decimal    | Per-question marks                    |
| created_at     | DateTime   | Auto                                  |

**Indexes:** `exam`

---

### 2.8 StudentAttempt

**Why it exists:** One attempt per student per exam. Prevents duplicate attempts and links to `StudentAnswer`.

| Field       | Type       | Notes                    |
|-------------|------------|--------------------------|
| student     | ForeignKey | FK → Student             |
| exam        | ForeignKey | FK → Exam                |
| started_at  | DateTime   | Auto                     |
| submitted_at| DateTime   | Null until submitted     |

**Constraints:** `UniqueConstraint(student, exam)` — enforces one attempt per student per exam.

**Indexes:** `student`, `exam`

---

### 2.9 StudentAnswer

**Why it exists:** Stores a student's selected option for each question within an attempt.

| Field           | Type       | Notes                      |
|-----------------|------------|----------------------------|
| attempt         | ForeignKey | FK → StudentAttempt        |
| question        | ForeignKey | FK → Question              |
| selected_option | CharField  | e.g. "A" or empty          |
| created_at      | DateTime   | Auto                       |

**Constraints:** `UniqueConstraint(attempt, question)` — one answer per question per attempt.

**Indexes:** `attempt`, `question`

**Application-level invariant:** The question must belong to the exam of the attempt. Enforced in views when creating `StudentAnswer`.

---

## 3. Relationship Structure

### Hierarchy

1. **User → Profile:** Each role has a OneToOne profile model (Teacher, Student, CollegeAdmin).
2. **Profile → College:** All three profiles have `ForeignKey` to College.
3. **Teacher → Exam:** `Exam.created_by` → Teacher.
4. **Exam → Question:** `Question.exam` → Exam.
5. **Student + Exam → StudentAttempt:** Composite unique on (student, exam).
6. **StudentAttempt + Question → StudentAnswer:** Composite unique on (attempt, question).

### Access Paths

| Query                           | Path                                      |
|---------------------------------|-------------------------------------------|
| Exams by college                | `Exam.objects.filter(created_by__college=college)` |
| Attempts for an exam            | `attempts` reverse relation on Exam       |
| Answers for an attempt          | `answers` reverse relation on StudentAttempt |
| Student's colleges              | `Student.objects.filter(user=user).values_list('college', flat=True)` |

---

## 4. Indexes and Constraints Summary

| Model        | Indexes                                           | Constraints                                                          |
|--------------|---------------------------------------------------|----------------------------------------------------------------------|
| CustomUser   | role                                              | —                                                                    |
| College      | code (unique)                                     | —                                                                    |
| Teacher      | college, employee_id                              | unique (college, employee_id) where employee_id non-empty            |
| Student      | college, roll_number                              | unique (college, roll_number) where roll_number non-empty            |
| CollegeAdmin | college                                           | —                                                                    |
| Exam         | test_code (unique), (start_time, end_time), created_by, result_published | end_time > start_time, negative_marking ≤ 0 |
| Question     | exam                                              | —                                                                    |
| StudentAttempt | student, exam                                   | unique (student, exam)                                               |
| StudentAnswer | attempt, question                                | unique (attempt, question)                                           |

---

## 5. Key Design Decisions

1. **Email as USERNAME_FIELD:** Standard for modern apps; `username = None` on `CustomUser`.
2. **Profile models (Teacher, Student, CollegeAdmin):** Separate OneToOne tables instead of one polymorphic table — cleaner and extensible.
3. **No College FK on Exam:** College is derived via `created_by.college` to avoid redundancy.
4. **test_code:** 8-char uppercase alphanumeric (no ambiguous chars like 0/O, 1/I) via `get_random_string`.
5. **UniqueConstraint on (student, exam):** Prevents duplicate attempts at the DB level.
6. **result_published on Exam:** Simple flag for result publishing control.

---

## 6. Django Configuration

Add to `settings.py`:

```python
AUTH_USER_MODEL = "examination_portal.CustomUser"
```

Install app in `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "examination_portal",
]
```
