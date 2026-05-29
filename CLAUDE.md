# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

美多商城 (MeiDuo Mall) — an e-commerce platform with a Django REST API backend and a static Vue.js frontend. Currently only the user/auth infrastructure is implemented (registration, login, SMS/email verification, JWT auth). The product, cart, order, and payment backends do not exist yet.

## Dev Commands

All commands run from the `testkb/` directory (where `manage.py` lives). The settings module is hardcoded to `testkb.settings.dev`.

```bash
# Django dev server (port 8000)
cd testkb && uv run manage.py runserver

# Celery worker (Redis broker on DB 7)
cd testkb && uv run celery -A celery_tasks.main worker -l info

# Database migrations
cd testkb && uv run manage.py makemigrations
cd testkb && uv run manage.py migrate

# Install all dependencies after cloning
uv sync

# Add a new dependency
uv add <package>

# Regenerate lockfile after changing pyproject.toml
uv lock
```

**Required services**: MySQL on `127.0.0.1:3306` (db: `testkb`, user: `testkb`, pass: `testkb`), Redis on `127.0.0.1:6379`.

The static frontend (`front_end_pc/`) is served separately — typically by Nginx on port 8080. There is no Django template rendering; all HTML is static.

## Architecture

### Import path trick

`settings/dev.py` does `sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))`. This means apps in `testkb/apps/` are importable as top-level modules: `from users.models import User`, not `from testkb.apps.users.models import User`. This applies project-wide.

### Layers

```
Static HTML+Vue.js (port 8080) ──CORS──▶ Django DRF API (port 8000)
                                            │
                                      ┌─────┼─────┐
                                      ▼     ▼     ▼
                                    MySQL  Redis  Celery
                                                    │
                                              ┌─────┴─────┐
                                              ▼           ▼
                                          SMS (云通讯)   Email (163 SMTP)
```

### Apps

- **`users`** (`testkb/apps/users/`) — Custom user model, registration, JWT login, profile, email verification. Uses `itsdangerous.TimedJSONWebSignatureSerializer` for email tokens.
- **`verifications`** (`testkb/apps/verifications/`) — SMS code generation and rate-limiting. Stores codes in Redis DB 2 with 300s TTL and a 60s send cooldown.

### Celery tasks (fire-and-forget, no result backend)

Located at `celery_tasks/` (separate from Django apps, but loads Django settings for model/email access):
- `celery_tasks.sms.tasks.send_sms_code` — Calls Yuntongxun (容联云通讯) SMS API
- `celery_tasks.email.tasks.send_verify_email` — Sends HTML email via Django's `send_mail()` with an inline HTML string (not a template file)

### Auth system

- Custom user model: `users.User` (extends `AbstractUser`), adds `mobile` and `email_active` fields. Table: `tb_users`.
- `AUTH_USER_MODEL = 'users.User'`
- `AUTHENTICATION_BACKENDS = ['users.utils.UsernameMobileAuthBackend']` — allows login with username OR mobile number.
- JWT via `rest_framework_simplejwt` with a custom serializer (`MyTokenObtainPairSerializer`) that adds `user_id`, `username`, `email`, `mobile` to the token payload and response.
- Login endpoint: `POST /authorizations/` (not `/api/token/`, which also exists but uses the stock serializer).

### Redis database layout

| DB | Purpose |
|----|---------|
| 0 | Default cache |
| 1 | Sessions |
| 2 | SMS verify codes (keys: `sms_{mobile}`, `send_flag_{mobile}`) |
| 7 | Celery broker |

### Frontend-backend contract

- API base URL is hardcoded in `front_end_pc/js/hosts.js`: `var host = 'http://127.0.0.1:8000'`
- JWT is stored in `localStorage` (remember-me) or `sessionStorage` (session-only) under keys `token`, `username`, `user_id`.
- Authenticated requests include the JWT via `Authorization: Bearer <token>` header (Axios does this via the DRF JWT auth class on the backend).
- Email verification link points to `http://127.0.0.1:8080/success_verify_email.html?token=...` — the frontend page then calls `GET /emails/verification/?token=...` to complete verification.

### Key patterns

- `CreateUserSerializer.create()` handles registration end-to-end: validates SMS code against Redis, creates the user in MySQL, and generates a JWT — all in one method.
- `User.generate_email_verify_url()` and `User.check_verify_email_token()` are defined on the model, not in a utility module.
- SMS sending uses Redis pipelines (`pl = redis_conn.pipeline()`) for atomic SETEX of the code + send flag.
- The `EmailSerializer.update()` method is overloaded — it updates the email field AND triggers the async verification email, rather than just persisting data.
