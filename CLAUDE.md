# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

美多商城 (MeiDuo Mall) — an e-commerce platform with a Django REST API backend and a static Vue.js frontend. Currently only the user/auth infrastructure is implemented (registration, login, SMS/email verification, JWT auth). The product, cart, order, and payment backends do not exist yet.

- **Python**: 3.11 (managed by uv, virtualenv at `.venv/` in project root)
- **Package manager**: uv (never pip)

## Dev Commands

The settings module is hardcoded to `testkb.settings.dev` in `manage.py`.

```bash
# Install all dependencies after cloning (run from project root)
uv sync

# Django dev server (port 8000) — run from testkb/
cd testkb && uv run manage.py runserver

# Celery worker (Redis broker on DB 7) — run from testkb/
cd testkb && uv run celery -A celery_tasks.main worker -l info

# Database migrations — run from testkb/
cd testkb && uv run manage.py makemigrations
cd testkb && uv run manage.py migrate

# Frontend static server (port 8080)
cd front_end_pc && uv run python -m http.server 8080

# Add a new dependency
uv add <package>

# Regenerate lockfile after changing pyproject.toml
uv lock
```

**Required services**: MySQL on `127.0.0.1:3306` (db: `testkb`, user: `testkb`, pass: `testkb`), Redis on `127.0.0.1:6379`.

The static frontend (`front_end_pc/`) is a standalone directory of HTML/CSS/JS files. In dev, it's served by Python's `http.server` on port 8080. In production, Nginx serves it on port 8080. There is no Django template rendering; all HTML is static.

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

- **`users`** (`testkb/apps/users/`) — Custom user model, registration, JWT login, profile, email verification. Registered in INSTALLED_APPS.
- **`verifications`** (`testkb/apps/verifications/`) — SMS code generation and rate-limiting. Stores codes in Redis DB 2 with 300s TTL and a 60s send cooldown. **Not registered in INSTALLED_APPS** (commented out in dev.py line 62), but its URLs are still routed via `urls.py` — the views work via direct imports.

### Celery tasks (fire-and-forget, no result backend)

Located at `testkb/celery_tasks/` (separate from Django apps, but loads Django settings for model/email access):
- `celery_tasks.sms.tasks.send_sms_code` — Calls Yuntongxun (容联云通讯) SMS API
- `celery_tasks.email.tasks.send_verify_email` — Sends HTML email via Django's `send_mail()` with an inline HTML string (not a template file)

### Yuntongxun SMS SDK (duplicated)

The Yuntongxun REST SDK exists in **two identical copies**:
- `testkb/libs/yuntongxun/` — used by the `verifications` app views
- `testkb/celery_tasks/sms/yuntongxun/` — used by the Celery SMS task

Both contain the same credentials (accountSid, accountToken, appId) and the same `CCP` singleton class. This is tech debt — they should be consolidated.

### Auth system

- Custom user model: `users.User` (extends `AbstractUser`), adds `mobile` and `email_active` fields. Table: `tb_users`.
- `AUTH_USER_MODEL = 'users.User'`
- `AUTHENTICATION_BACKENDS = ['users.utils.UsernameMobileAuthBackend']` — allows login with username OR mobile number.
- JWT via `rest_framework_simplejwt` with a custom serializer (`MyTokenObtainPairSerializer`) that adds `user_id`, `username`, `email`, `mobile` to the token payload and response.
- Login endpoint: `POST /authorizations/` (not `/api/token/`, which also exists but uses the stock serializer).
- JWT auth header: `Authorization: JWT <token>` (configured via `AUTH_HEADER_TYPES: ("JWT",)` in SIMPLE_JWT settings). The token type prefix is **JWT**, not Bearer.
- `SIMPLE_JWT.ACCESS_TOKEN_LIFETIME` = 1 day, `REFRESH_TOKEN_LIFETIME` = 1 day.

### Redis database layout

| DB | Purpose |
|----|---------|
| 0 | Default cache |
| 1 | Sessions |
| 2 | SMS verify codes (keys: `sms_{mobile}`, `send_flag_{mobile}`) |
| 7 | Celery broker |

### Custom exception handler

`testkb/utils/exceptions.py` — replaces DRF's default exception handler. Catches `DatabaseError` and `RedisError`, logs them, and returns HTTP 507 (Insufficient Storage) with `{'message': '服务器内部错误'}`. Configured via `REST_FRAMEWORK['EXCEPTION_HANDLER']`.

### BaseModel (unused)

`testkb/utils/models.py` defines `BaseModel(Models.Model)` with `create_time` and `update_time` fields (abstract). Currently unused — the `users.User` model has it commented out. Available for future models.

### Settings files

- **`testkb/settings/dev.py`** — Active settings (hardcoded in manage.py). MySQL, Redis, DRF, JWT, CORS, email all configured.
- **`testkb/settings/prod.py`** — Skeleton production settings (uses SQLite, no DRF/Redis/CORS). Not yet production-ready.
- **`testkb/wsgi.py`** — References `testkb.settings` (the package, not `dev`), so it won't work without setting `DJANGO_SETTINGS_MODULE` externally.

### Credentials (hardcoded — security debt)

- **Email** (163 SMTP): `sunweiimin@163.com` / `WYIMJIKKCNGMSAAK`
- **SMS** (Yuntongxun): accountSid `8a216da8662360a4016696e56a9b365a`, accountToken `1eb7343c59284d428411203da32d358c`, appId `8a216da8662360a4016696e56af43661`
- **Django SECRET_KEY**: `qw02w@_3uf9i)a69wj=f902n8$aw-fh1bzd-2a61mk))6as4=t`

All credentials should be moved to environment variables before production deployment.

### Frontend-backend contract

- API base URL is hardcoded in `front_end_pc/js/hosts.js`: `var host = 'http://127.0.0.1:8000'`
- JWT is stored in `localStorage` (remember-me) or `sessionStorage` (session-only) under keys `token`, `username`, `user_id`.
- Authenticated requests include the JWT via `Authorization: JWT <token>` header. The frontend's Axios interceptor writes `Bearer` but the DRF `AUTH_HEADER_TYPES` setting uses `JWT` — check this mismatch if auth fails.
- Email verification link points to `http://127.0.0.1:8080/success_verify_email.html?token=...` — the frontend page then calls `GET /emails/verification/?token=...` to complete verification.

### Key patterns

- `CreateUserSerializer.create()` handles registration end-to-end: validates SMS code against Redis, creates the user in MySQL, and generates a JWT — all in one method.
- `User.generate_email_verify_url()` and `User.check_verify_email_token()` are defined on the model, not in a utility module. Uses `itsdangerous.URLSafeTimedSerializer` (not the deprecated `TimedJSONWebSignatureSerializer`).
- SMS sending uses Redis pipelines (`pl = redis_conn.pipeline()`) for atomic SETEX of the code + send flag.
- The `EmailSerializer.update()` method is overloaded — it updates the email field AND triggers the async verification email, rather than just persisting data.
