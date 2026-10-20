# Prompt to Product – AI Web Challenge

**Official Hackathon Management Platform**  
*Organized by SSRS Group of Companies*

---

## 📌 Project Overview

**Prompt to Product – AI Web Challenge** is a production-ready, full-stack web application engineered for managing team registrations, problem statement publishing, deployed website link submissions, and jury evaluations for the online AI Web Challenge organized by **SSRS Group of Companies**.

### Key Highlights
- **Persistent MySQL Database:** Complete schema handling users, teams, team members, problem statements, submissions, submission history, evaluations, rankings, announcements, FAQs, site settings, and audit logs.
- **Dynamic 1–4 Member Team Registration:** Automated team registration ID generation (`P2P-2026-XXXX`), Indian mobile number validation, and email normalization.
- **Deployed Website Link Submission:** Strictly accepts live public HTTP/HTTPS URLs (no raw ZIP/source file uploads to the portal).
- **Comprehensive Super Admin Management:** Full control over website copy, event branding, logo inspection & selection, problem statements, operational deadlines, submission grading out of 60, and result publication without source code redeployment.
- **Official External Integrations:** Embedded WhatsApp Community access and official Unstop opportunity registration & submission links.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla ES6+), Inter & Poppins Typography |
| **Backend** | Python 3.10+ / Flask |
| **Database** | MySQL 8.0 |
| **ORM** | Flask-SQLAlchemy, PyMySQL |
| **Database Migrations** | Flask-Migrate (Alembic) |
| **Authentication & Sessions** | Flask-Login, Secure Session Cookies, Rate Limiting |
| **Password Hashing** | Werkzeug (`generate_password_hash` / `check_password_hash`) |
| **Form Security** | Flask-WTF, CSRF Protection, Server-Side Validation |
| **Email Service** | Flask-Mail with SMTP (with safe logging fallback) |
| **Production Server** | Waitress (Windows) / Gunicorn (Linux) |
| **Configuration** | Environment variables via `.env` / `python-dotenv` |
| **Testing** | Pytest |

---

## 📁 Application Structure

```text
C:\ssrsgc\Unstop hackathon\
├── app/
│   ├── __init__.py               # Flask application factory
│   ├── extensions.py             # db, migrate, login_manager, csrf, mail
│   ├── models/                   # SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── user.py               # User model (team_leader, admin, super_admin)
│   │   ├── team.py               # Team & TeamMember models
│   │   ├── submission.py         # Submission & SubmissionHistory models
│   │   ├── content.py            # ProblemStatement, Announcements, FAQs, Settings, AuditLogs
│   │   └── evaluation.py         # Evaluation & Result models
│   ├── routes/                   # Application Blueprints
│   │   ├── __init__.py
│   │   ├── public.py             # Home, About, Problem Statement, Rules, Contact
│   │   ├── auth.py               # Login, Admin Login, Logout, Password Reset
│   │   ├── registration.py       # Team registration & success views
│   │   ├── dashboard.py          # Participant leader dashboard & settings
│   │   ├── submissions.py        # Website-link submission & confirmation
│   │   └── admin.py              # Super Admin control center (all 16 modules)
│   ├── services/                 # Business logic & external services
│   │   ├── __init__.py
│   │   ├── email_service.py      # SMTP dispatcher with safe simulation fallback
│   │   ├── registration_service.py# Validation, unique ID, atomic registration
│   │   ├── submission_service.py # URL validation, duplicate checks, audit trail
│   │   └── settings_service.py   # Dynamic settings, status calculator, logo resolver
│   ├── static/
│   │   ├── css/
│   │   │   ├── styles.css        # Premium Dark Navy & Gold public theme
│   │   │   └── admin.css         # Admin panel stylesheet
│   │   ├── js/
│   │   │   ├── main.js           # Navbar, FAQ accordion, alerts
│   │   │   └── registration.js   # Dynamic Add/Remove team members (1-4)
│   │   └── images/
│   │       ├── official_logo.jpg # Official uploaded event logo
│   │       ├── ssrsgc_logo.png   # SSRS Group of Companies brand icon
│   │       └── ssrsgc_banner.png # SSRS Group of Companies banner
│   └── templates/                # Jinja2 templates
│       ├── base.html             # Master layout
│       ├── index.html            # Public homepage
│       ├── about.html            # About challenge page
│       ├── problem_statement.html# Dedicated problem statement page
│       ├── rules.html            # Rules & guidelines
│       ├── contact.html          # Contact form & support
│       ├── auth/                 # Authentication & registration templates
│       ├── dashboard/            # Participant dashboard & submission templates
│       ├── admin/                # Admin portal templates (all 16 sections)
│       └── errors/               # 400, 403, 404, 429, 500 error pages
├── migrations/                   # Alembic schema migrations
├── scripts/
│   ├── create_admin.py           # CLI tool to create Super Admin
│   └── seed_data.py              # Database seeding script (defaults, FAQs, Problem Statement)
├── tests/                        # Automated Pytest suite
│   ├── test_auth.py
│   ├── test_registration.py
│   ├── test_submission.py
│   └── test_admin.py
├── config.py                     # Configuration classes (Dev, Prod, Test)
├── requirements.txt              # Production Python dependencies
├── run.py                        # Application entry point
├── .env.example                  # Environment template
├── .env                          # Local environment secrets
├── .gitignore                    # Git exclusions
└── README.md                     # Documentation
```

---

## 🚀 Local Windows Setup Guide (PowerShell)

Follow these exact commands to set up and run the portal locally on Windows:

### 1. Navigate to Project Directory
```powershell
Set-Location "C:\ssrsgc\Unstop hackathon"
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` (already created with local development values):
```powershell
Copy-Item .env.example .env
```

Ensure your `.env` contains:
```env
FLASK_ENV=development
SECRET_KEY=ssrsgc-p2p-a78df6e102bc4501a3cd495817a0ee44
FLASK_APP=run.py

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=prompt_to_product
MYSQL_USER=root
MYSQL_PASSWORD=admin

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@ssrsgc.com

PUBLIC_BASE_URL=http://127.0.0.1:5000
REGISTRATION_OPEN=true
EMAIL_VERIFICATION_REQUIRED=false
SESSION_COOKIE_SECURE=false
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Initialize Database & Seed Content
```powershell
# Create tables and seed initial Problem Statement, FAQs, and Site Settings
python scripts/seed_data.py
```

### 5. Setup Initial Super Admin Account
Run the secure CLI command:
```powershell
python scripts/create_admin.py
```
*Default testing credentials created:*
- **Email:** `admin@ssrsgc.com`
- **Password:** `AdminPassword2026!`
- **Role:** `super_admin`

### 6. Run Automated Test Suite
```powershell
$env:PYTHONPATH = "C:\ssrsgc\Unstop hackathon"
python -m pytest tests/
```

### 7. Start the Flask Application
```powershell
python run.py
```
Open your browser at: **`http://127.0.0.1:5000`**  
Admin Login: **`http://127.0.0.1:5000/admin/login`**

---

## 🌐 Official External URLs

- **WhatsApp Community:** `https://chat.whatsapp.com/F4yqR3OBRnGARB9rV9CF7K`
- **Official Unstop Opportunity:** `https://unstop.com/p/prompt-to-product-ai-web-challenge-ssrs-group-of-companies-1772617`
- **Official Unstop Submission Destination:** Configurable via Admin Dashboard (initially points to the opportunity page).

---

## 🔒 Security Architecture

1. **Role-Based Access Control (RBAC):** Backend route guards (`@admin_required`, `@super_admin_required`) protect all `/admin` routes. Regular participants and public visitors are redirected away.
2. **Data Ownership Protection:** Team leaders can only view and edit their own team data; IDOR vulnerabilities are prevented by querying records against `current_user.id`.
3. **Strict URL Validation:** Submissions accept only public HTTP/HTTPS web links. Raw project files, ZIP archives, or arbitrary file uploads are not accepted. The server never executes or crawls submitted links.
4. **CSRF Protection:** Flask-WTF CSRF tokens are injected and verified across all HTML forms.
5. **Secure Authentication:** Passwords hashed with Werkzeug PBKDF2/scrypt, brute-force rate limiting on login attempts, and timed one-hour password reset tokens.
6. **Full Audit Logging:** All sensitive administrative operations (role changes, team status updates, evaluation grading, results publication) are recorded with timestamps, actor IDs, and metadata.

---

## 🏆 Evaluation & Grading System

Administrators evaluate submissions directly in the `/admin/evaluations` panel across six criteria (each scored out of 10 for a total of 60):
1. **Functionality & Execution** (10 Marks)
2. **Innovation & AI Integration** (10 Marks)
3. **Prompt Engineering & Workflow** (10 Marks)
4. **UI/UX Design & Responsiveness** (10 Marks)
5. **Real-World Practical Impact** (10 Marks)
6. **Code & Architecture Quality** (10 Marks)

Once scores are finalized, rankings are calculated automatically. The Super Admin can publish or withhold the Top 3 winners with one confirmed action.

---

## 📜 License & Intellectual Property

&copy; 2026 SSRS Group of Companies. All rights reserved.
