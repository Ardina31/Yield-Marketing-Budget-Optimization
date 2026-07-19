# Yield — Marketing Budget Optimization Platform

A production-style SaaS application that helps businesses optimize digital
marketing budgets using campaign performance data and non-linear
optimization (SciPy SLSQP).

Rebuilt from a single-file Flask prototype into a layered application with
Blueprints, a service layer, a normalized database schema, and a bespoke
design system inspired by tools like Stripe, Linear, and Google Analytics.

## Features

- **Multi-strategy budget optimizer** — Maximize ROI, Maximize Conversions,
  Minimize Cost, or a Balanced blend, powered by SciPy's SLSQP solver with a
  diminishing-returns model (`log1p`) so early spend matters more than the
  last dollar.
- **Campaign management** — create, edit, search, filter, sort, and
  paginate campaigns; drill into per-campaign history.
- **CSV / Excel import** — auto-maps common column names ("Spend",
  "Ad Spend", "Amount Spent" → Cost, etc.), auto-creates channels, and
  upserts metrics per reporting period so campaigns accumulate history
  across months instead of being overwritten.
- **Dashboard** — total campaigns, budget, ROI, conversion rate, CTR, CPC,
  CPA, best channel, spend trend, budget allocation donut, top campaigns by
  ROI, and a live quick-optimization preview.
- **Reporting** — polished PDF (ReportLab), Excel with an embedded chart
  (openpyxl), and CSV exports, with a history of generated reports.
- **Notifications & activity log** — in-app notification center and a full
  audit trail of logins, uploads, optimizations, and exports.
- **Auth & roles** — Admin / Agent / Viewer roles, hashed passwords,
  CSRF-protected forms, session cookies.
- **Light & dark mode**, responsive layout down to mobile, toasts, skeleton
  loaders, and an accessible, keyboard-friendly component set.

## Architecture

```
Routes (HTTP only) → Services (business logic) → Models (SQLAlchemy) → DB
```

```
app/
├── __init__.py          # application factory
├── extensions.py        # db, login_manager, csrf
├── models/              # user, channel, campaign, campaign_metric,
│                        # optimization, report, notification,
│                        # activity_log, setting
├── auth/                # login, register, logout
├── dashboard/           # KPI overview
├── campaigns/           # CRUD + CSV/Excel import
├── optimization/        # run optimizer, view history
├── reports/             # PDF / Excel / CSV export
├── settings/            # profile, preferences, security
├── api/                 # JSON endpoints (notifications)
├── services/            # optimizer, analytics, campaign, import,
│                        # report, notification, activity
├── utils/               # decorators, constants, formatters
├── templates/
└── static/{css,js,images}
config.py                # Dev / Prod / Testing config classes
run.py                    # dev entrypoint
seed.py                   # demo data generator
```

## Database schema

| Table | Purpose |
|---|---|
| `users` | Identity, role, theme preference |
| `channels` | Marketing channel catalogue (Google Ads, Meta, Email, …) |
| `campaigns` | One row per campaign |
| `campaign_metrics` | One row per campaign **per reporting period** — this is what lets a campaign accumulate multiple months of history |
| `optimization_runs` / `optimization_allocations` | Saved optimizer results |
| `reports` | Export history |
| `notifications` | In-app notification center |
| `activity_logs` | Audit trail |
| `settings` | Per-user preferences |

## Getting started

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then edit SECRET_KEY etc.

python seed.py                  # creates tables + a demo admin + sample data
python run.py                   # http://localhost:5000
```

Demo login: **admin@yield.app** / **admin123**

To start from a completely empty workspace instead of demo data, skip
`seed.py` and just run `python run.py` — it creates tables and default
channels, then register your own account from the app.

### Running tests

```bash
pip install pytest
pytest
```

## Optimization strategies

| Strategy | What it does |
|---|---|
| Maximize ROI | Shifts budget toward channels with the strongest return on ad spend |
| Maximize Conversions | Shifts budget toward channels producing the most conversions per dollar |
| Minimize Cost | Holds current projected performance while spending as little as possible |
| Balanced | Blends ROI, conversions, and cost-efficiency (50/35/15 weighting) |

Every channel's allowed spend is bounded between 20% and 300% of its
current spend (configurable in `config.py`) to keep recommendations
realistic, and projected gains apply a conservative 85% execution factor.

## Notes for production

- Set a strong `SECRET_KEY` and `DATABASE_URL` (Postgres recommended) via
  environment variables — `ProductionConfig` will refuse to start with the
  default dev secret.
- Put the app behind Gunicorn + a reverse proxy (`gunicorn "run:app"`).
- Add `Flask-Migrate` if you need schema migrations beyond `db.create_all()`.
