import secrets
from urllib.parse import urlparse
from datetime import datetime
from app.extensions import db
from app.models.submission import Submission, SubmissionHistory
from app.models.content import AuditLog
from app.services.settings_service import SettingsService
from app.services.email_service import EmailService


class SubmissionService:
    @staticmethod
    def validate_website_url(url):
        if not url:
            return False, 'Website URL is required.'
        url = url.strip()
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                return False, 'Only public HTTP or HTTPS URLs are accepted (e.g., https://your-project.vercel.app).'
            if not parsed.netloc:
                return False, 'Please provide a valid domain or host (e.g., your-project.com).'
            # Reject localhost and internal loops for production submissions if desired, but allow for testing
            hostname = parsed.hostname or ''
            if '.' not in hostname and hostname not in ('localhost', '127.0.0.1'):
                return False, 'URL must include a valid top-level domain.'
            return True, url
        except Exception:
            return False, 'Malformed or invalid URL syntax.'

    @staticmethod
    def generate_submission_id():
        while True:
            rand_code = secrets.token_hex(2).upper()
            sub_id = f"SUB-2026-{rand_code}"
            if not Submission.query.filter_by(submission_id=sub_id).first():
                return sub_id

    @classmethod
    def can_submit_or_edit(cls, team, is_edit=False):
        # 1. Team-level explicit permissions
        if is_edit and team.allow_edit:
            return True, "Team edit permitted by administrator."
        if not is_edit and team.allow_resubmit:
            return True, "Team resubmission permitted by administrator."

        # 2. Check global submissions open flag
        if not SettingsService.get_setting('submissions_open', 'true').lower() == 'true':
            return False, "Submissions are currently closed by the administrator."

        # 3. Check dates
        now = datetime.utcnow()
        sub_start = SettingsService.parse_datetime(SettingsService.get_setting('submission_start_date'))
        sub_end = SettingsService.parse_datetime(SettingsService.get_setting('submission_deadline'))

        if sub_start and now < sub_start:
            return False, f"Submissions will open on {sub_start.strftime('%d %b %Y %I:%M %p')} IST."
        if sub_end and now > sub_end:
            return False, "The submission deadline has passed. Submissions and edits are locked."

        # 4. If editing an existing submission, check post-submission edit settings
        if is_edit:
            allow_edits = SettingsService.get_setting('allow_post_submit_edits', 'false').lower() == 'true'
            if not allow_edits:
                return False, "Modifying submitted projects is currently locked."

        return True, "Submissions are open."

    @classmethod
    def submit_project(cls, team, user, website_url, project_description=''):
        # Check permission
        can_proceed, reason = cls.can_submit_or_edit(team, is_edit=False)
        if not can_proceed and not team.allow_resubmit:
            return False, reason

        # Validate URL
        valid, result = cls.validate_website_url(website_url)
        if not valid:
            return False, result
        clean_url = result

        # Check existing submission
        existing = Submission.query.filter_by(team_id=team.id).first()
        if existing and not team.allow_resubmit:
            allow_resub = SettingsService.get_setting('allow_resubmission', 'false').lower() == 'true'
            if not allow_resub:
                return False, "Your team has already submitted a project. Resubmissions are not permitted."

        try:
            if existing:
                # Update existing submission
                existing.website_url = clean_url
                existing.project_description = project_description.strip() if project_description else None
                existing.updated_at = datetime.utcnow()
                existing.status = 'submitted'
                submission = existing
                change_type = 'reopened_submission' if team.allow_resubmit else 'user_edit'
                # Reset team-level override once used
                team.allow_resubmit = False
            else:
                submission_id = cls.generate_submission_id()
                submission = Submission(
                    submission_id=submission_id,
                    team_id=team.id,
                    website_url=clean_url,
                    project_description=project_description.strip() if project_description else None,
                    status='submitted',
                    submitted_at=datetime.utcnow()
                )
                db.session.add(submission)
                db.session.flush()
                change_type = 'initial_submission'

            # Append to history
            history = SubmissionHistory(
                submission_id=submission.id,
                website_url=clean_url,
                project_description=project_description.strip() if project_description else None,
                changed_by=user.id,
                change_type=change_type,
                changed_at=datetime.utcnow()
            )
            db.session.add(history)

            AuditLog.record(
                action='project_submitted',
                entity_type='submission',
                entity_id=submission.submission_id,
                actor_id=user.id,
                metadata={'team_id': team.id, 'change_type': change_type}
            )

            db.session.commit()

            # Email notification
            EmailService.send_submission_confirmation(user, team, submission)

            return True, submission

        except Exception as e:
            db.session.rollback()
            return False, f"Failed to record submission: {str(e)}"

    @classmethod
    def edit_submission(cls, submission, user, website_url, project_description=''):
        team = submission.team
        can_proceed, reason = cls.can_submit_or_edit(team, is_edit=True)
        if not can_proceed and not (user.is_admin or team.allow_edit):
            return False, reason

        valid, result = cls.validate_website_url(website_url)
        if not valid:
            return False, result
        clean_url = result

        try:
            submission.website_url = clean_url
            submission.project_description = project_description.strip() if project_description else None
            submission.updated_at = datetime.utcnow()

            change_type = 'admin_edit' if user.is_admin else 'user_edit'
            history = SubmissionHistory(
                submission_id=submission.id,
                website_url=clean_url,
                project_description=project_description.strip() if project_description else None,
                changed_by=user.id,
                change_type=change_type,
                changed_at=datetime.utcnow()
            )
            db.session.add(history)

            # If user edit was granted via allow_edit, reset it
            if not user.is_admin and team.allow_edit:
                team.allow_edit = False

            AuditLog.record(
                action='submission_edited',
                entity_type='submission',
                entity_id=submission.submission_id,
                actor_id=user.id,
                metadata={'change_type': change_type}
            )

            db.session.commit()
            return True, submission

        except Exception as e:
            db.session.rollback()
            return False, f"Failed to update submission: {str(e)}"
