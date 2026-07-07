# OpenG2P Enderase Youth

This repository contains the Enderase Youth OpenG2P local stack:

- the Enderase Youth registry on Odoo
- the Enderase dashboard, API, metrics sync, and ClickHouse analytics store
- PBMS running as a separate Odoo instance and database
- native Odoo Survey extended with ODK Central offline collection support

The local compose file is intended for development and integration testing.

## Services

Run the stack from this directory:

```bash
docker compose up -d
```

Main local endpoints:

| Service | URL | Notes |
| --- | --- | --- |
| Enderase Registry Odoo | `http://localhost:8069` | Main registry, Survey, ODK integration, embedded dashboard menu |
| PBMS Odoo | `http://localhost:8070` | PBMS runs on its own database |
| Dashboard web | `http://localhost:8080` | Next.js dashboard UI |
| Dashboard API | `http://localhost:8000` | FastAPI dashboard API |
| PBMS staff portal API | `http://localhost:8001` | PBMS background/task API |
| ClickHouse HTTP | `http://localhost:8123` | Analytics storage |
| Postgres registry DB | `localhost:5432` | Default DB name `enderase` |
| Postgres PBMS DB | `localhost:5433` | Default DB name `pbms_odoo` |

Default local Odoo credentials are controlled by the compose environment and default to:

```text
Email: admin@example.com
Password: admin
```

## Odoo Addons

The registry Odoo service mounts these local addons:

| Addon | Purpose |
| --- | --- |
| `g2p_enderase_youth_registry` | Enderase registry extensions for individuals, members, beneficiaries, startups, associations, and related lookup data |
| `g2p_ati_embed` | Embedded dashboard configuration and menu integration |
| `enderase_theme` | Enderase backend UI theme and home menu styling |
| `g2p_survey` | Enderase extension for native Survey plus ODK Central workflows |

The native `survey` app and its `gamification` dependency are **not** vendored. The
OpenG2P base image strips both out of Odoo core, so `../odoo/Dockerfile` copies them
back in from the official `odoo:17.0` image. They stay untouched stock Odoo — only
`g2p_survey` (the extension) lives in this repository.

The registry Odoo bootstrap installs and updates:

```text
g2p_enderase_youth_registry,g2p_ati_embed,gamification,survey,g2p_survey,enderase_theme
```

## Survey And ODK

Enderase uses the real Odoo `survey` module as the source of truth for forms and responses. The `g2p_survey` addon does not create a separate survey model. It extends:

- `survey.survey` with ODK delivery settings, push/import buttons, a generated XLSForm (`.xlsx`), and sync status fields
- `survey.user_input` with response source and ODK submission metadata
- `survey.user_input.line` indirectly through Odoo's native answer-saving APIs

This means online Odoo responses and offline ODK imports both appear in the same native Odoo Survey participation screens.

The native Survey app stays at the top level (outside Enderase Registry). `g2p_survey`
only adds an ODK integration submenu inside it. Survey menus are available from:

- `Surveys / Surveys`
- `Surveys / Participations`
- `Surveys / Questions & Answers`
- `Surveys / ODK Integration / ODK Users`
- `Surveys / ODK Integration / ODK Servers`

The public online survey form uses Odoo's native route:

```text
/survey/start/<survey_access_token>
```

The survey footer is branded as:

```text
Powered by Enderase
```

See [g2p_survey/README.md](g2p_survey/README.md) for the detailed ODK workflow.

### Surveys that register Enderase members

`g2p_enderase_youth_registry` lets a survey provision an Enderase member from its
answers. On the survey form (Options tab) tick **Register Enderase Member**, then on
each question set **Enderase Member Field** to the `res.partner` field the answer
should populate (Full Name, Phone, Email, Date of Birth, Region, Occupation, etc.).

When a response reaches the *done* state — whether completed online or imported from
ODK Central — a `res.partner` is created with `is_enderase_member = True` (record
status *Submitted*, membership status *Applied*), the mapped fields are filled,
choice answers are matched to the registry lookups (region, profession, …) by code,
and the response's `Registered Member` field links to it. The g2p background-task
worker then assigns the member's `unique_id` / Enderase Registry ID asynchronously.

The module ships the full production **Enderase Youth Membership Registration**
survey (`data/enderase_member_survey.xml`) with 43 questions. Its select questions
pull their choices **from the registry lookup models** (`g2p_odk_choice_model`, value
= record `code`), including the cascading **Region → Zone → Woreda** selects. Pushing
the survey to ODK generates the XLSForm from this configuration (no file upload); the
choices, `choice_filter` cascades, `relevant`, and `constraint` columns are all built
from the questions. On import, each submission node is matched to a `res.partner`
field by the question's `ODK Field Name`, and choice codes resolve to the lookups by
`code`.

## PBMS Separation

PBMS runs independently from the registry Odoo instance:

- PBMS Odoo service: `pbms-odoo`
- PBMS database service: `pbms-postgres`
- PBMS database: `pbms_odoo`

The PBMS background services can read the registry database when program access, entitlement, eligibility, or beneficiary search flows need registry data, but PBMS does not share the main Odoo registry database as its own application database.

## Dashboard

The dashboard lives under `enderase_dashboard`:

- `enderase_dashboard/web` is the Next.js UI
- `enderase_dashboard/api` is the FastAPI API
- `enderase_dashboard/metrics-sync` copies registry metrics into ClickHouse
- `enderase_dashboard/clickhouse/init` contains ClickHouse initialization SQL

See [enderase_dashboard/README.md](enderase_dashboard/README.md) and [enderase_dashboard/docs/DASHBOARD_ARCHITECTURE.md](enderase_dashboard/docs/DASHBOARD_ARCHITECTURE.md).

## Development Checks

Useful local checks:

```bash
docker compose config
python3 -c "import pathlib, xml.etree.ElementTree as ET; [ET.parse(p) for p in pathlib.Path('g2p_survey').rglob('*.xml')]"
python3 -c "import ast, pathlib; [ast.parse(p.read_text()) for p in pathlib.Path('g2p_survey').rglob('*.py')]"
docker compose ps
```

To force Odoo to reload changed addons:

```bash
docker compose up -d --force-recreate odoo
```

The Odoo service health endpoint is:

```text
http://localhost:8069/web/health
```
