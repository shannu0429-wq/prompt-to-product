# Production Deployment & Database Guide
**Prompt to Product – AI Web Challenge**  
**Organized by SSRS Group of Companies**

---

## 1. Production Architecture Overview

- **Web Application:** Python Flask 3.1.2 running on **Gunicorn 23.0.0** (Production WSGI server with 2 worker processes, 4 threads, 120s timeout).
- **Reverse Proxy & TLS:** Render Cloud Edge / Cloudflare with **Werkzeug ProxyFix** (`x_for=1, x_proto=1, x_host=1, x_prefix=1`) ensuring all redirects, session cookies, and links use strict **HTTPS**.
- **Database Engine:** Managed, persistent cloud MySQL (or Render PostgreSQL) connected via SQLAlchemy 2.0 with connection pooling (`pool_recycle=280`, `pool_pre_ping=True`).
- **Health Check Endpoint:** `GET /health` returns JSON health status and confirms database connectivity safely without exposing secrets.
- **Source Control & Auto-Deploy:** GitHub repository `https://github.com/shannu0429-wq/prompt-to-product` on branch `main`. Approved commits automatically trigger zero-downtime builds.

---

## 2. Environment Variables Reference (Render Environment Tab)

Configure these in Render Dashboard &rarr; **prompt-to-product** &rarr; **Environment**:

| Variable Name | Required | Default / Description |
|---|---|---|
| `FLASK_ENV` | Yes | `production` |
| `SECRET_KEY` | Yes | High-entropy random string for CSRF and session cookie signing. |
| `DATABASE_URL` | Yes | Cloud MySQL URI (e.g. `mysql+pymysql://user:pass@host:port/dbname?charset=utf8mb4`) or Render PostgreSQL URI. |
| `SESSION_COOKIE_SECURE` | Yes | `true` (enforces HTTPS-only cookies). |
| `PUBLIC_BASE_URL` | Optional | Your public domain (e.g. `https://prompt-to-product.onrender.com`). |
| `REGISTRATION_OPEN` | Optional | `true` |
| `EMAIL_VERIFICATION_REQUIRED` | Optional | `false` |
| `MAIL_SERVER` | Optional | `smtp.gmail.com` |
| `MAIL_PORT` | Optional | `587` |
| `MAIL_USE_TLS` | Optional | `true` |
| `MAIL_USERNAME` | Optional | SMTP email username for notifications. |
| `MAIL_PASSWORD` | Optional | SMTP app password. |
| `ADMIN_EMAIL` | Optional | `admin@ssrsgc.com` |
| `ADMIN_PASSWORD` | Optional | `AdminPassword2026!` |

---

## 3. Online Database Setup Options

### Option A: Free Cloud MySQL via TiDB Serverless (Recommended for Native MySQL)
1. Sign up at [https://tidbcloud.com/](https://tidbcloud.com/) (Free Forever, 5GB storage, MySQL 8.0 wire-compatible).
2. Click **Create Cluster** &rarr; select **Serverless (Free)**.
3. In cluster dashboard, click **Connect** &rarr; choose **SQLAlchemy / PyMySQL**.
4. Copy the connection string format:
   ```text
   mysql+pymysql://<username>:<password>@gateway01.<region>.prod.aws.tidbcloud.com:4000/<database_name>?ssl_ca=/etc/ssl/certs/ca-certificates.crt
   ```
5. Paste it as `DATABASE_URL` in your Render Environment settings.

### Option B: Render Managed PostgreSQL (1-Click on Render)
1. In your Render Dashboard, click **New +** &rarr; **PostgreSQL**.
2. Name it `prompt-to-product-db`, select region, click **Create Database**.
3. Under **Connections**, copy the **Internal Database URL** (e.g. `postgres://...`).
4. Paste it as `DATABASE_URL` in your Render Web Service Environment. Our adapter automatically converts it to `postgresql://` and runs all schema migrations.

---

## 4. Database Backup & Disaster Recovery

### Automatic Schema & Seed on Startup
When a fresh database is connected, the application automatically inspects the database on startup. If tables do not exist, it automatically runs:
1. `db.create_all()` to create all 14 relational tables.
2. `SettingsService.seed_defaults()` to populate default event settings, timing schedules, and FAQs.
3. `ProblemStatement` v1 initialization with the published challenge brief.
4. Default Super Admin creation (`admin@ssrsgc.com`).

### Manual Backup Procedure
To dump existing data to a local SQL file:
```powershell
# Using mysqldump for local or remote MySQL:
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe" -h <HOST> -P <PORT> -u <USER> -p<PASSWORD> <DATABASE> --result-file="backups/prompt_to_product_backup.sql"
```

### Manual Restore Procedure
To restore a backup into a new database instance:
```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -h <HOST> -P <PORT> -u <USER> -p<PASSWORD> <DATABASE> < "backups/prompt_to_product_backup.sql"
```

### Content Migration Helper Script
You can also use our built-in Python migration utility:
```powershell
# Export all content to JSON backup:
python scripts/db_migration_helper.py

# Sync to a remote database URL:
$env:DATABASE_URL = "mysql+pymysql://user:pass@remotehost:3306/dbname"
python scripts/db_migration_helper.py --sync
```

---

## 5. Live Admin Dashboard Controls

Located at: `/admin` (Login: `/admin/login`)

- **Overview Statistics:** Live counts of Total Teams, Registered Leaders, Total Participants, Projects Submitted, Pending Reviews, Shortlisted Projects, and Problem Statement versions.
- **Auto-Refresh Toggle:** Periodic 30-second background refresh to monitor incoming team registrations and submissions live during the event without duplicate actions.
- **Team Management:** Search, status filtering (`pending`, `verified`, `suspended`), member inspection, and one-click CSV export.
- **Problem Statement Versioning:** Add, Edit, Delete, Publish, and Unpublish versions with audit logging.
- **Schedule Time Access:** Configure release timestamp, submission window opening, and submission deadline directly from `/admin/problem-statement`.
- **Project Submissions:** View submitted public links, update evaluation statuses, edit URLs with full change audit trail, and export submissions to CSV.
- **Announcements & FAQs:** Instant CRUD for public event updates.
