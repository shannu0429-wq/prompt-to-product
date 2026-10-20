import os
from datetime import datetime
from app.models.content import SiteSetting
from app.extensions import db

DEFAULT_SETTINGS = {
    'event_title': 'Prompt to Product – AI Web Challenge',
    'event_subtitle': 'Turn Your Ideas into Intelligent Digital Products.',
    'event_description': 'Join the AI Web Challenge by SSRS Group of Companies. Use AI tools and prompt engineering to transform an innovative idea into a functional, responsive web application.',
    'organizer_name': 'SSRS Group of Companies',
    'organizer_tagline': 'Empowering Next-Gen Innovators',
    'whatsapp_group_url': 'https://chat.whatsapp.com/F4yqR3OBRnGARB9rV9CF7K',
    'unstop_opportunity_url': 'https://unstop.com/p/prompt-to-product-ai-web-challenge-ssrs-group-of-companies-1772617',
    'unstop_submission_url': 'https://unstop.com/p/prompt-to-product-ai-web-challenge-ssrs-group-of-companies-1772617',
    'contact_email': 'support@ssrsgc.com',
    'contact_phone': '+91 98765 43210',
    'registration_start_date': '2026-10-01 00:00:00',
    'registration_end_date': '2026-11-25 23:59:59',
    'problem_statement_release_date': '2026-10-25 10:00:00',
    'submission_start_date': '2026-10-25 12:00:00',
    'submission_deadline': '2026-11-30 23:59:59',
    'submissions_open': 'true',
    'allow_resubmission': 'false',
    'allow_post_submit_edits': 'false',
    'event_status_override': 'auto',  # 'auto', 'registration_open', 'submissions_open', 'evaluating', 'completed', 'closed'
    'active_logo_path': '/static/images/official_logo.jpg',
    'banner_logo_path': '/static/images/ssrsgc_banner.png',
    'results_published': 'false',
    'participation_certificates_enabled': 'true',
    'announcement_banner': '',
    'submission_confirmation_text': 'Your project has been recorded in our database. Note that you must also submit on Unstop to complete your hackathon participation!',
}


class SettingsService:
    @staticmethod
    def get_setting(key, default=None):
        val = SiteSetting.get(key)
        if val is not None:
            return val
        return DEFAULT_SETTINGS.get(key, default)

    @staticmethod
    def set_setting(key, value):
        return SiteSetting.set(key, value)

    @staticmethod
    def get_all_settings():
        settings = dict(DEFAULT_SETTINGS)
        db_settings = SiteSetting.query.all()
        for s in db_settings:
            settings[s.setting_key] = s.setting_value
        return settings

    @staticmethod
    def seed_defaults():
        for key, val in DEFAULT_SETTINGS.items():
            existing = SiteSetting.query.filter_by(setting_key=key).first()
            if not existing:
                s = SiteSetting(setting_key=key, setting_value=val)
                db.session.add(s)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    @staticmethod
    def parse_datetime(dt_str):
        if not dt_str:
            return None
        formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M', '%Y-%m-%d']
        for fmt in formats:
            try:
                return datetime.strptime(dt_str.strip(), fmt)
            except ValueError:
                continue
        return None

    @classmethod
    def get_event_status(cls):
        override = cls.get_setting('event_status_override', 'auto')
        if override and override != 'auto':
            status_map = {
                'registration_open': ('Registration Open', 'badge-success'),
                'submissions_open': ('Submissions Active', 'badge-primary'),
                'evaluating': ('Under Evaluation', 'badge-warning'),
                'completed': ('Challenge Completed', 'badge-info'),
                'closed': ('Registration Closed', 'badge-danger'),
            }
            return status_map.get(override, (override.replace('_', ' ').title(), 'badge-secondary'))

        now = datetime.utcnow()
        reg_start = cls.parse_datetime(cls.get_setting('registration_start_date'))
        reg_end = cls.parse_datetime(cls.get_setting('registration_end_date'))
        sub_start = cls.parse_datetime(cls.get_setting('submission_start_date'))
        sub_end = cls.parse_datetime(cls.get_setting('submission_deadline'))

        if reg_start and now < reg_start:
            return ('Coming Soon', 'badge-info')
        if reg_end and now <= reg_end:
            return ('Registration Open', 'badge-success')
        if sub_start and sub_end and now >= sub_start and now <= sub_end:
            return ('Submissions Active', 'badge-primary')
        if sub_end and now > sub_end:
            results_pub = cls.get_setting('results_published', 'false').lower() == 'true'
            if results_pub:
                return ('Winners Announced', 'badge-gold')
            return ('Under Evaluation', 'badge-warning')

        return ('Registration Active', 'badge-success')

    @classmethod
    def are_submissions_open(cls, team=None):
        if team and team.allow_resubmit:
            return True

        sub_flag = cls.get_setting('submissions_open', 'true').lower() == 'true'
        if not sub_flag:
            return False

        now = datetime.utcnow()
        sub_end = cls.parse_datetime(cls.get_setting('submission_deadline'))
        if sub_end and now > sub_end:
            return False

        sub_start = cls.parse_datetime(cls.get_setting('submission_start_date'))
        if sub_start and now < sub_start:
            return False

        return True

    @classmethod
    def is_registration_open(cls):
        reg_flag = cls.get_setting('registration_open', 'true').lower() == 'true'
        if not reg_flag:
            return False

        now = datetime.utcnow()
        reg_end = cls.parse_datetime(cls.get_setting('registration_end_date'))
        if reg_end and now > reg_end:
            return False

        reg_start = cls.parse_datetime(cls.get_setting('registration_start_date'))
        if reg_start and now < reg_start:
            return False

        return True

    @classmethod
    def is_problem_statement_released(cls):
        release_dt = cls.parse_datetime(cls.get_setting('problem_statement_release_date'))
        if not release_dt:
            return True
        return datetime.utcnow() >= release_dt

    @classmethod
    def is_submission_started(cls):
        start_dt = cls.parse_datetime(cls.get_setting('submission_start_date'))
        if not start_dt:
            return True
        return datetime.utcnow() >= start_dt

    @classmethod
    def is_submission_deadline_passed(cls):
        end_dt = cls.parse_datetime(cls.get_setting('submission_deadline'))
        if not end_dt:
            return False
        return datetime.utcnow() > end_dt

    @classmethod
    def get_timeline(cls):
        now = datetime.utcnow()
        prob_release = cls.parse_datetime(cls.get_setting('problem_statement_release_date'))
        sub_start = cls.parse_datetime(cls.get_setting('submission_start_date'))
        sub_end = cls.parse_datetime(cls.get_setting('submission_deadline'))
        reg_end = cls.parse_datetime(cls.get_setting('registration_end_date'))

        return {
            'problem_release_date': cls.get_setting('problem_statement_release_date'),
            'is_problem_released': (not prob_release) or (now >= prob_release),
            'submission_start_date': cls.get_setting('submission_start_date'),
            'is_submission_started': (not sub_start) or (now >= sub_start),
            'submission_deadline': cls.get_setting('submission_deadline'),
            'is_submission_closed': bool(sub_end and now > sub_end),
            'registration_deadline': cls.get_setting('registration_end_date'),
            'is_registration_closed': bool(reg_end and now > reg_end),
        }

    @classmethod
    def get_active_logo(cls):
        path = cls.get_setting('active_logo_path', '/static/images/official_logo.jpg')
        return path
