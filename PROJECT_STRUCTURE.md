# Examination Portal — Project Structure & Configuration

## Folder Structure

```
Examination Portal/
├── config/                      # Project configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py              # Shared settings
│   │   ├── development.py       # Dev overrides
│   │   └── production.py        # Prod overrides
│   ├── urls.py                  # Root URLconf
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/                    # Authentication & user management
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                # CustomUser
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
├── colleges/                    # College, Teacher, Student, CollegeAdmin
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                # College, Teacher, Student, CollegeAdmin
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
├── exams/                       # Exam & Question management
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                # Exam, Question
│   ├── views.py                 # CSV upload will live here
│   ├── urls.py
│   └── admin.py
│
├── results/                     # Attempts, answers, scores
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                # StudentAttempt, StudentAnswer
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
├── templates/                   # Project-wide templates
│   └── base.html (to add)
│
├── static/                      # CSS, JS, images
│
├── media/                       # User uploads (CSV, etc.)
│   └── uploads/                 # Recommended: uploads/csv/ for CSV files
│
├── manage.py
├── requirements.txt
├── .env.example
└── .env                         # Create from .env.example (git-ignored)
```

---

## Installed Apps

| App | Purpose |
|-----|---------|
| `django.contrib.admin` | Admin interface |
| `django.contrib.auth` | Auth, sessions |
| `django.contrib.contenttypes` | Content types framework |
| `django.contrib.sessions` | Session framework |
| `django.contrib.messages` | Flash messages |
| `django.contrib.staticfiles` | Static file serving |
| `accounts` | Custom user, login, registration |
| `colleges` | College, Teacher, Student, CollegeAdmin |
| `exams` | Exam, Question, CSV import |
| `results` | StudentAttempt, StudentAnswer, scores |

---

## Settings Configuration

### Custom User Model

```python
AUTH_USER_MODEL = "accounts.CustomUser"
```

- CustomUser lives in `accounts` app.
- Must be set before first migration.
- All auth and foreign keys to User point to this model.

### Split Settings (base / development / production)

- **base.py** — Common settings, env vars, INSTALLED_APPS, AUTH_USER_MODEL.
- **development.py** — Imports from base, sets DEBUG=True.
- **production.py** — Imports from base, sets DEBUG=False; add secure cookies, HTTPS, etc.

Activation via `DJANGO_SETTINGS_MODULE`:

- Dev: `config.settings.development`
- Prod: `config.settings.production`

---

## Media Configuration (CSV Upload)

| Setting | Value | Purpose |
|---------|-------|---------|
| `MEDIA_URL` | `/media/` | URL prefix for media files |
| `MEDIA_ROOT` | `./media` (or env) | Filesystem path for uploads |

Suggested layout for CSV uploads:

- `media/uploads/csv/` — CSV files
- `media/uploads/csv/2025/02/` — Optional date-based subdirs

In `urls.py`, media is served in DEBUG:

```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Production: serve media via Nginx, S3, or another static/media server.

---

## URL Routing Structure

| Prefix | App | Purpose |
|--------|-----|---------|
| `/admin/` | Django admin | Admin panel |
| `/` | accounts | Login, logout, register, dashboard |
| `/colleges/` | colleges | College management, profiles |
| `/exams/` | exams | Exam list, create, attempt, CSV import |
| `/results/` | results | Scores, leaderboard, publish |

Each app has its own `urls.py`; root `config/urls.py` includes them.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | (required in prod) | Secret key |
| `DJANGO_DEBUG` | `True` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hosts |
| `DJANGO_SETTINGS_MODULE` | `config.settings.development` | Settings module |
| `MEDIA_URL` | `/media/` | Media URL prefix |
| `MEDIA_ROOT` | `./media` | Media root path |
| `DATABASE_URL` | (optional) | For PostgreSQL, etc. |

Loaded via `python-dotenv` in `base.py`; `.env` should be created from `.env.example`.

---

## App Responsibilities

| App | Models (from schema) | Responsibilities |
|-----|----------------------|------------------|
| **accounts** | CustomUser | Auth, login, registration, role-based redirect |
| **colleges** | College, Teacher, Student, CollegeAdmin | Colleges and profiles |
| **exams** | Exam, Question | Exam CRUD, CSV import, test taking |
| **results** | StudentAttempt, StudentAnswer | Scores, leaderboard, publish control |

---

## Next Steps

1. Copy `.env.example` to `.env` and set `DJANGO_SECRET_KEY`.
2. Split models from `examination_portal/models.py` into `accounts`, `colleges`, `exams`, and `results`.
3. Run `python manage.py makemigrations` and `python manage.py migrate`.
4. Implement views and templates in each app.
