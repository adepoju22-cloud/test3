# Security Compliance Dashboard (Local, 100% Free)

A fully local Security Compliance Dashboard that simulates how enterprise
platforms such as Prisma Cloud, Wiz, Microsoft Defender for Cloud, and AWS
Config evaluate cloud resources against security baselines &mdash; without
needing any cloud account, subscription, or paid service.

It reads a JSON resource inventory, evaluates it against YAML-defined
compliance rules mapped to **CIS**, **NIST**, and **ISO 27001**, stores the
results in **SQLite**, exposes them through a **FastAPI** REST API, and
visualizes them in **Grafana**. PDF and CSV reports are generated with
ReportLab and Pandas. Everything runs with a single `docker compose up`.

---

## 1. Project Overview

| Capability | How it's implemented |
|---|---|
| Resource inventory | `app/resources/resources.json` (30 sample resources across 6 types) |
| Rule engine | YAML files in `app/rules/` (42 rules), auto-discovered at scan time |
| Framework mapping | Every rule maps to CIS, NIST, and ISO 27001 |
| Scanner | `app/scanner/engine.py` evaluates every applicable rule per resource |
| Storage | SQLite via SQLAlchemy (`app/database/`) |
| REST API | FastAPI (`app/api/routes.py`), Swagger UI at `/docs` |
| Dashboards | Grafana, auto-provisioned, reading the SQLite file directly |
| Reports | PDF (ReportLab) and CSV (Pandas) via `/reports/pdf` and `/reports/csv` |
| Logging | Rotating file handler at `logs/scanner.log` |
| Containerization | `Dockerfile` + `docker-compose.yml` |

---

## 2. Architecture Diagram

```
                         resources.json
                       (resource inventory)
                              |
                              v
                     YAML rule files
                     app/rules/*.yaml
                     (auto-discovered)
                              |
                              v
                       Scanner Engine
                     (loader + engine)
                              |
                          Findings
                              v
                       SQLite Database
                     compliance_results
                          /        \
                         v          v
                 FastAPI REST API   Grafana Dashboards
                 /scan /results     (reads SQLite file
                 /summary /reports   via SQLite plugin)
```

---

## 3. Folder Structure

```
security-compliance-dashboard/
├── app/
│   ├── api/                 # FastAPI route definitions
│   │   └── routes.py
│   ├── scanner/              # Resource/rule loaders + evaluation engine
│   │   ├── loader.py
│   │   └── engine.py
│   ├── database/              # SQLAlchemy engine, models, CRUD
│   │   ├── db.py
│   │   ├── models.py
│   │   └── crud.py
│   ├── reports/                # PDF and CSV report generators
│   │   ├── pdf_report.py
│   │   └── csv_report.py
│   ├── rules/                   # YAML compliance rules (auto-discovered)
│   │   ├── cis.yaml
│   │   └── framework_mapping.json
│   ├── resources/                 # Resource inventory + generator script
│   │   ├── resources.json
│   │   └── generate_resources.py
│   ├── models/                     # Pydantic schemas
│   │   └── schemas.py
│   ├── services/                    # Orchestration layer
│   │   ├── scan_service.py
│   │   └── summary_service.py
│   ├── utils/                        # Config + logging
│   │   ├── config.py
│   │   └── logger.py
│   └── main.py                        # FastAPI application entry point
├── database/                            # SQLite file lives here at runtime
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/datasource.yml
│   │   └── dashboards/dashboard.yml
│   └── dashboards/compliance_dashboard.json
├── docker/                                 # Optional helper scripts
├── tests/
│   ├── test_scanner.py
│   └── test_api.py
├── logs/                                     # scanner.log written here
├── reports_output/                             # Generated PDF/CSV reports
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 4. Installation (Run Without Docker)

**Requirements:** Python 3.12+

```bash
# 1. Clone / unzip the project, then enter it
cd security-compliance-dashboard

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment config
cp .env.example .env

# 5. (Optional) Regenerate sample resources/rules
python -m app.resources.generate_resources

# 6. Start the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser to:
- **Swagger UI:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/

---

## 5. Docker Usage (Full Stack: API + Grafana)

**Requirements:** Docker + Docker Compose

```bash
docker compose up --build
```

This single command will:
1. Build the FastAPI application image.
2. Start the API container on **http://localhost:8000**.
3. Start Grafana on **http://localhost:3000** (default login `admin` / `admin`).
4. Auto-provision the SQLite datasource and the compliance dashboard.

To stop everything:

```bash
docker compose down
```

To wipe the local database and start fresh:

```bash
docker compose down -v
rm -f database/compliance.db
docker compose up --build
```

---

## 6. Running Your First Scan

The database is empty until a scan is triggered. Run one via the API:

```bash
curl -X POST http://localhost:8000/scan
```

Expected response:

```json
{
  "message": "Scan completed successfully",
  "resources_scanned": 30,
  "rules_evaluated": 42,
  "findings_generated": 210,
  "passed": 123,
  "failed": 87,
  "scan_time": "2026-06-19T12:00:00.000000"
}
```

---

## 7. API Usage

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/scan` | Run a full compliance scan and persist results |
| `GET`  | `/results` | List stored results (filters: `status`, `severity`, `resource_type`) |
| `GET`  | `/summary` | Aggregate compliance %, severity breakdown, top violated rules |
| `GET`  | `/critical` | All Critical-severity failed findings |
| `GET`  | `/failed` | All failed findings |
| `GET`  | `/resources` | Raw resource inventory |
| `GET`  | `/rules` | All loaded compliance rules |
| `GET`  | `/reports/pdf` | Download a generated PDF report |
| `GET`  | `/reports/csv` | Download a generated CSV report |

Examples:

```bash
curl http://localhost:8000/summary
curl "http://localhost:8000/results?status=FAIL&severity=Critical"
curl -o report.pdf http://localhost:8000/reports/pdf
curl -o report.csv http://localhost:8000/reports/csv
```

Full interactive documentation (Swagger) is always available at `/docs`,
and the OpenAPI schema at `/openapi.json`.

---

## 8. Grafana Dashboard

After `docker compose up --build`:

1. Go to **http://localhost:3000** (login `admin` / `admin`).
2. Navigate to **Dashboards → Security Compliance → Security Compliance Dashboard**.
3. The dashboard is pre-loaded with:
   - Compliance %, Total Findings, Passed, Failed
   - Critical / High / Medium / Low counts
   - Findings by Severity (pie chart)
   - Findings by Framework (bar chart)
   - Top Violated Rules (table)
   - Compliance Trend (time series, across multiple scans)
   - All Findings (full table)

> **Note:** Grafana queries the SQLite file directly through the
> `frser-sqlite-datasource` community plugin (installed automatically by
> `docker-compose.yml` via `GF_INSTALL_PLUGINS`). Re-run `POST /scan`
> periodically (or build a small cron/script) to populate the
> *Compliance Trend* panel with multiple data points over time.

### Screenshots

> _Add screenshots here after your first local run:_
> - `docs/screenshots/dashboard-overview.png`
> - `docs/screenshots/swagger-ui.png`
> - `docs/screenshots/pdf-report.png`

---

## 9. Reports

- **PDF** (`GET /reports/pdf`): title page, executive summary, compliance
  score table, severity bar chart, top 5 recommendations, and a full table
  of failed controls.
- **CSV** (`GET /reports/csv`): every stored finding, suitable for Excel,
  audit evidence, or further analysis in Pandas.

Both are written to `reports_output/` and also returned for direct download.

---

## 10. Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

`tests/test_scanner.py` validates the rule engine and loader logic in
isolation. `tests/test_api.py` exercises the full FastAPI surface against
an isolated in-memory SQLite database.

---

## 11. Extending the Project (No Code Changes Required)

- **Add a new rule:** drop a new `*.yaml` file into `app/rules/` following
  the schema below — the scanner discovers it automatically on the next scan.
- **Add a new resource:** add an entry to `app/resources/resources.json`.
- **Add a new resource type:** add it to the `ResourceType` enum in
  `app/models/schemas.py`, then write rules targeting it.

**Rule schema:**

```yaml
rules:
  - id: CIS-099
    title: Example Rule Title
    description: What this rule checks and why it matters.
    severity: High                  # Critical | High | Medium | Low
    resource_type: VirtualMachine   # Must match a ResourceType value
    field: some_property_name       # Looked up in resource.properties
    operator: equals                # equals | not_equals | contains | exists | greater_than | less_than
    expected_value: true
    recommendation: How to remediate this finding.
    framework_mapping:
      cis: CIS-099
      nist: SC-99
      iso27001: A.8.99
```

---

## 12. Logging

Every scan is logged to `logs/scanner.log` (rotating, 5 MB x 5 backups) and
to stdout, including resource/rule counts and the PASS/FAIL breakdown of
each run.

---

## 13. Verifying Every Feature Works (Step-by-Step)

1. `docker compose up --build` — wait for both containers to report healthy.
2. `curl http://localhost:8000/` — should return `{"status": "running", ...}`.
3. `curl http://localhost:8000/resources | jq length` — should return `30`.
4. `curl http://localhost:8000/rules | jq length` — should return `42`.
5. `curl -X POST http://localhost:8000/scan` — should return `findings_generated: 210`.
6. `curl http://localhost:8000/summary` — should return a `compliance_percentage`.
7. `curl http://localhost:8000/critical | jq length` — should return the Critical FAIL count.
8. `curl -o report.pdf http://localhost:8000/reports/pdf` — open the PDF and confirm it renders.
9. `curl -o report.csv http://localhost:8000/reports/csv` — open in Excel/Sheets.
10. Open `http://localhost:8000/docs` — confirm Swagger renders and every endpoint is listed.
11. Open `http://localhost:3000` — confirm the "Security Compliance Dashboard" loads with live data.
12. `pytest tests/ -v` — confirm all unit and API tests pass.

---

## 14. Future Improvements

- Add JWT-based authentication and role-based access control to the API.
- Schedule recurring scans (APScheduler or a cron sidecar) to populate the
  Grafana Compliance Trend panel automatically.
- Add a remediation workflow that opens a ticket (e.g. local Jira/GitLab
  instance) for each new Critical finding.
- Support additional frameworks (SOC 2, PCI DSS, HIPAA) via extra mapping
  fields on each rule.
- Add a lightweight React/Next.js front-end as an alternative to Grafana.
- Persist scan history per run (rather than replacing prior results) to
  support true trend analysis and drift detection over time.

---

## 15. Tech Stack

Python 3.12 &middot; FastAPI &middot; SQLAlchemy &middot; SQLite &middot;
Pydantic &middot; PyYAML &middot; Pandas &middot; ReportLab &middot;
Jinja2 &middot; Docker &middot; Docker Compose &middot; Grafana
