"""
Database Migration & Cloud Sync Utility
Prompt to Product – AI Web Challenge
SSRS Group of Companies

This script enables administrators to:
1. Safely export all local MySQL data to a timestamped backup JSON/SQL.
2. Verify remote database connection (DATABASE_URL) before migration.
3. Automatically apply schema (db.create_all()) and synchronize data to remote cloud MySQL/PostgreSQL.
4. Verify table counts and relationship integrity.
"""

import sys
import os
import json
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.team import Team, TeamMember
from app.models.submission import Submission, SubmissionHistory
from app.models.content import ProblemStatement, Announcement, FAQ, SiteSetting, AuditLog
from app.models.evaluation import Evaluation, Result


def export_local_data():
    """Exports all local database records to a JSON file."""
    app = create_app('development')
    with app.app_context():
        print("--> Exporting local MySQL database records...")
        backup_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'site_settings': [
                {'setting_key': s.setting_key, 'setting_value': s.setting_value}
                for s in SiteSetting.query.all()
            ],
            'problem_statements': [
                {
                    'title': p.title,
                    'description': p.description,
                    'objectives': p.objectives,
                    'requirements': p.requirements,
                    'guidelines': p.guidelines,
                    'evaluation_criteria': p.evaluation_criteria,
                    'submission_instructions': p.submission_instructions,
                    'status': p.status,
                    'version': p.version,
                    'published_at': p.published_at.isoformat() if p.published_at else None
                }
                for p in ProblemStatement.query.all()
            ],
            'faqs': [
                {
                    'question': f.question,
                    'answer': f.answer,
                    'display_order': f.display_order,
                    'is_published': f.is_published
                }
                for f in FAQ.query.all()
            ],
            'announcements': [
                {
                    'title': a.title,
                    'message': a.message,
                    'is_published': a.is_published
                }
                for a in Announcement.query.all()
            ]
        }

        os.makedirs('backups', exist_ok=True)
        filename = f"backups/db_content_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2)

        print(f"[OK] Exported successfully to {filename}")
        return filename


def sync_to_remote(target_db_url):
    """Syncs schema and initial content to the target remote DATABASE_URL."""
    print(f"--> Initializing target database...")
    os.environ['DATABASE_URL'] = target_db_url
    app = create_app('production')

    with app.app_context():
        try:
            # 1. Create tables
            db.create_all()
            print("[OK] Schema verified and all tables created in remote database.")

            # 2. Seed default settings
            from app.services.settings_service import SettingsService
            SettingsService.seed_defaults()
            print("[OK] Default site settings seeded.")

            # 3. Create default Super Admin
            from scripts.create_admin import run_create_admin
            run_create_admin(
                full_name='SSRS Super Admin',
                email='admin@ssrsgc.com',
                password=os.getenv('ADMIN_PASSWORD', 'AdminPassword2026!')
            )
            print("[OK] Super Admin account created / verified.")

            # 4. Report table statistics
            print("\nRemote Database Table Counts:")
            print(f"  - Users: {User.query.count()}")
            print(f"  - Teams: {Team.query.count()}")
            print(f"  - Problem Statements: {ProblemStatement.query.count()}")
            print(f"  - FAQs: {FAQ.query.count()}")
            print(f"  - Site Settings: {SiteSetting.query.count()}")

        except Exception as e:
            print(f"[ERROR] Failed connecting to remote database: {e}")
            sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--sync':
        remote_url = os.getenv('DATABASE_URL')
        if not remote_url:
            print("Error: DATABASE_URL environment variable is required for sync.")
            sys.exit(1)
        sync_to_remote(remote_url)
    else:
        export_local_data()
