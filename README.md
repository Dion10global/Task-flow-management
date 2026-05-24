# TaskFlow — Cloud Task Management SaaS

> ICC 7211 — Cloud Application Development | HIT MTech Cloud Computing

A full-stack, production-ready Task Management SaaS platform built with **Django REST Framework** on the backend and a responsive **vanilla JS + HTML5** frontend, deployed on a PaaS provider following the **Twelve-Factor App** methodology.

---

## ✨ Features

| Feature | Details |
|---|---|
| JWT Auth | Register, Login, Token Refresh, Logout (blacklist), Change Password |
| RBAC | Admin (full access) / Member (assigned projects only) |
| Projects | CRUD, member management, progress tracking, stats |
| Tasks | Kanban board, status updates, priority, due dates, comments, activity log |
| API | RESTful, OpenAPI 3.0 docs at `/api/docs/` |
| Security | HTTPS, security headers, rate limiting, CORS, input sanitisation, parameterised queries |
| CI/CD | GitHub Actions — test on push, deploy on merge to `main` |

---

## 🚀 Quick Start

### 1. Clone & setup

```bash
git clone <your-repo-url>
cd taskflow

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment

```bash
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY
```

### 3. Run

```bash
python manage.py migrate
python manage.py createsuperuser   # optional admin account
python manage.py runserver
```

Visit **http://localhost:8000** — you'll see the landing page.

| Route | Description |
|---|---|
| `/` | Landing page |
| `/login/` | Sign in |
| `/register/` | Create account |
| `/dashboard/` | App dashboard (auth required) |
| `/projects/` | Project list |
| `/projects/<id>/` | Kanban board |
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc |
| `/admin/` | Django admin |

---

## 🧪 Running Tests

```bash
pytest                        # all tests + coverage
pytest tests/unit/            # unit tests only
pytest tests/integration/     # integration tests only
pytest --cov-report=html      # open htmlcov/index.html
```

**Minimum coverage target: 70%**

---

## 📁 Project Structure

```
taskflow/
├── taskflow/               # Django project config
│   ├── settings.py         # Env-aware settings (django-environ)
│   ├── urls.py             # Root URL config
│   └── wsgi.py
├── apps/
│   ├── core/               # Shared: middleware, pagination, exceptions, views
│   ├── accounts/           # Custom User, JWT auth, RBAC permissions
│   ├── projects/           # Projects + members
│   └── tasks/              # Tasks, comments, activity log
├── frontend/
│   ├── static/
│   │   ├── css/main.css    # Full design system (dark, amber accents)
│   │   └── js/             # api.js, app.js, dashboard.js, projects.js, project-detail.js
│   └── templates/          # HTML5 templates (landing, auth, dashboard, kanban)
├── tests/
│   ├── factories.py        # factory_boy factories
│   ├── unit/               # 15+ unit tests
│   └── integration/        # 10+ integration / API tests
├── .github/workflows/ci.yml # CI/CD pipeline
├── Procfile                # Heroku/PaaS process config
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## 🔌 API Overview

Base URL: `/api/v1/`

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register/` | Create account |
| POST | `/auth/login/` | Obtain JWT pair |
| POST | `/auth/logout/` | Blacklist refresh token |
| POST | `/auth/token/refresh/` | Refresh access token |
| GET/PATCH | `/auth/me/` | Own profile |
| POST | `/auth/change-password/` | Change password |

### Projects
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/projects/` | List / Create |
| GET/PATCH/DELETE | `/projects/<id>/` | Retrieve / Update / Delete |
| GET | `/projects/<id>/stats/` | Task breakdown stats |
| GET/POST | `/projects/<id>/members/` | List / Add members |
| DELETE | `/projects/<id>/members/<id>/` | Remove member |

### Tasks
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/projects/<id>/tasks/` | List / Create tasks |
| GET/PATCH/DELETE | `/tasks/<id>/` | Retrieve / Update / Delete |
| PATCH | `/tasks/<id>/status/` | Real-time status update |
| GET/POST | `/tasks/<id>/comments/` | Comments |
| GET | `/tasks/<id>/activity/` | Audit log |
| GET | `/tasks/me/` | My assigned tasks |

---

## 🔐 Security Controls

- **JWT** with short-lived access tokens (60 min) + rotating refresh tokens (7 days)
- **RBAC**: Admin vs Member — enforced at queryset level, not just view level
- **Rate limiting**: 10 req/min on auth endpoints
- **Input sanitisation**: bleach on all user-supplied text fields
- **SQL injection prevention**: Django ORM with parameterised queries throughout
- **CORS**: Configurable allowed origins via env var
- **Security headers**: X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy via custom middleware
- **HTTPS + HSTS**: Enforced in production (DEBUG=False)

---

## ☁️ Deployment

### Heroku (example)

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:essential-0
heroku config:set SECRET_KEY="..." DEBUG=False ALLOWED_HOSTS="your-app.herokuapp.com"
git push heroku main
```

### Environment Variables (required in production)

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key (50+ chars) |
| `DEBUG` | `False` in production |
| `ALLOWED_HOSTS` | Comma-separated hosts |
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Default: 60 |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Default: 7 |

---

## 🏗️ Built With

- **Django 4.2** + **Django REST Framework 3.15**
- **SimpleJWT** — JWT authentication
- **drf-spectacular** — OpenAPI 3.0 schema generation
- **django-environ** — Twelve-Factor config
- **WhiteNoise** — Static file serving
- **bleach** — Input sanitisation
- **factory-boy + pytest-django** — Testing
- **GitHub Actions** — CI/CD

---

*ICC 7211 Practical Assignment — HIT School of Information Science & Technology*
