# SSPA400 Learning Management System

SSPA400 is a free, role-based LMS for English instruction. The deployed application uses Django, PostgreSQL, Bootstrap, and progressive web app features. Keeping one backend avoids splitting authentication and learner records across the older Django site and separate prototype stacks.

## Project structure

```text
config/                      Django settings and URL routing
lms/
  management/commands/      Idempotent production seed and optional demo data
  migrations/               Database schema history
  static/lms/               CSS, JavaScript, listening and pathway clients
  templates/lms/            Public, student, instructor, and admin screens
  tests/                     Regression and LMS workflow tests
  forms.py                   Validated account and authoring forms
  models.py                  LMS and existing SSPA400 data models
  portal_views.py            Student, instructor, and LMS admin workflows
  services.py                Grading, progress, completion, and certificate rules
  views.py                   Existing public lessons and Firebase session exchange
build.sh                     Render build, migrate, collectstatic, and seed
Procfile                     Gunicorn start command
requirements.txt             Python dependencies
```

## Local setup

1. Create and activate a Python 3.12+ virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Export the environment variables below in your shell or configure them in your preferred local environment loader. `.env` files are ignored by Git but are not loaded automatically.
4. Run `python manage.py migrate`.
5. Run `python manage.py seed` to create departments, catalog categories, and the free starter course.
6. Create an owner account with `python manage.py createsuperuser`, or set the `DJANGO_SUPERUSER_*` variables before running the seed.
7. Start the app with `python manage.py runserver` and open `http://127.0.0.1:8000/`.

## Required production environment

```dotenv
APP_ENV=production
DEBUG=False
SECRET_KEY=<long-random-secret>
DATABASE_URL=<render-postgres-url>
ALLOWED_HOSTS=sspa400-public.onrender.com
CSRF_TRUSTED_ORIGINS=https://sspa400-public.onrender.com

DJANGO_SUPERUSER_USERNAME=<owner-username>
DJANGO_SUPERUSER_EMAIL=<owner-email>
DJANGO_SUPERUSER_PASSWORD=<strong-unique-password>
```

The seed command never creates a hardcoded administrator. Keep production secrets in Render environment variables, not in source control.

## Firebase Google sign-in

Set the Firebase web application values on Render:

```dotenv
FIREBASE_API_KEY=...
FIREBASE_AUTH_DOMAIN=sspa400.firebaseapp.com
FIREBASE_PROJECT_ID=sspa400
FIREBASE_STORAGE_BUCKET=...
FIREBASE_MESSAGING_SENDER_ID=...
FIREBASE_APP_ID=...
FIREBASE_CREDENTIALS=<complete-service-account-json-on-one-line>
```

In Firebase Console:

1. Enable the Google provider under Authentication > Sign-in method.
2. Add `sspa400-public.onrender.com` and `localhost` under Authentication > Settings > Authorized domains.
3. Confirm the web app uses the same project as the service-account JSON.

The browser obtains a Firebase ID token. Django verifies that token server-side, creates or updates the local account profile, establishes the Django session, and redirects to profile setup or My Learning. Username/password login remains available when Firebase is unavailable.

## Password reset email

Without SMTP settings, reset messages print to the local console. Configure these values on Render to deliver email:

```dotenv
SMTP_HOST=...
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_USE_TLS=True
DEFAULT_FROM_EMAIL=SSPA400 LMS <noreply@example.com>
```

## Roles and access

- **Student:** enrolls in any free published course, tracks progress, takes quizzes, submits assignments, joins discussions, and receives certificates.
- **Instructor:** creates and publishes owned courses, modules, lessons, listening activities, quizzes, and assignments; reviews work in the gradebook.
- **Admin:** manages all users, instructor approvals, categories, courses, departments, and records.

Public instructor registration creates an approval request. An admin grants the Instructor role from `/manage/users/`. Admin accounts are only created through a trusted environment or Django management command.

## Tests and deployment

Run all checks before deployment:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --noinput
```

Render uses `build.sh`, which installs dependencies, applies migrations, collects static files, and runs the idempotent seed. Gunicorn starts the web process from `Procfile`.
