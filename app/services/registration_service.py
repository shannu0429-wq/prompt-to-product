import re
import secrets
from app.extensions import db
from app.models.user import User
from app.models.team import Team, TeamMember
from app.models.content import AuditLog
from app.services.email_service import EmailService

INDIAN_PHONE_REGEX = re.compile(r'^[6-9]\d{9}$')
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


class RegistrationService:
    @staticmethod
    def normalize_email(email):
        return email.strip().lower() if email else ''

    @staticmethod
    def validate_phone(phone):
        if not phone:
            return False
        cleaned = re.sub(r'[\s\-+()]', '', phone)
        if cleaned.startswith('91') and len(cleaned) == 12:
            cleaned = cleaned[2:]
        elif cleaned.startswith('0') and len(cleaned) == 11:
            cleaned = cleaned[1:]
        return bool(INDIAN_PHONE_REGEX.match(cleaned)), cleaned

    @staticmethod
    def generate_registration_id():
        while True:
            rand_code = secrets.token_hex(2).upper()  # 4 characters
            reg_id = f"P2P-2026-{rand_code}"
            if not Team.query.filter_by(registration_id=reg_id).first():
                return reg_id

    @classmethod
    def register_team(cls, form_data):
        """
        Processes team leader registration and team member creation.
        Returns (success: bool, result_or_errors: Team|dict)
        """
        errors = {}

        # 1. Validate Leader Fields
        full_name = form_data.get('leader_name', '').strip()
        email = cls.normalize_email(form_data.get('leader_email', ''))
        phone = form_data.get('leader_phone', '').strip()
        password = form_data.get('leader_password', '')
        confirm_password = form_data.get('leader_confirm_password', '')
        college = form_data.get('leader_college', '').strip()
        city = form_data.get('leader_city', '').strip()
        state = form_data.get('leader_state', '').strip()

        if not full_name or len(full_name) < 2:
            errors['leader_name'] = 'Full name must be at least 2 characters.'

        if not email or not EMAIL_REGEX.match(email):
            errors['leader_email'] = 'A valid email address is required.'
        elif User.query.filter_by(email=email).first():
            errors['leader_email'] = 'An account with this email already exists.'

        is_valid_phone, clean_phone = cls.validate_phone(phone)
        if not is_valid_phone:
            errors['leader_phone'] = 'Please enter a valid 10-digit Indian mobile number.'

        if not password or len(password) < 8:
            errors['leader_password'] = 'Password must be at least 8 characters long.'
        elif password != confirm_password:
            errors['leader_confirm_password'] = 'Passwords do not match.'

        if not college:
            errors['leader_college'] = 'College or organization is required.'
        if not city:
            errors['leader_city'] = 'City is required.'
        if not state:
            errors['leader_state'] = 'State is required.'

        # 2. Validate Team Fields
        team_name = form_data.get('team_name', '').strip()
        if not team_name or len(team_name) < 2:
            errors['team_name'] = 'Team name must be at least 2 characters.'
        elif Team.query.filter_by(team_name=team_name).first():
            errors['team_name'] = 'A team with this name has already registered.'

        # 3. Validate Team Members
        try:
            team_size = int(form_data.get('team_size', 1))
        except (ValueError, TypeError):
            team_size = 1

        if team_size < 1 or team_size > 4:
            errors['team_size'] = 'Team size must be between 1 and 4 members.'

        additional_members = []
        member_emails = {email}

        for i in range(1, team_size):
            m_name = form_data.get(f'member_{i}_name', '').strip()
            m_email = cls.normalize_email(form_data.get(f'member_{i}_email', ''))
            m_phone = form_data.get(f'member_{i}_phone', '').strip()
            m_college = form_data.get(f'member_{i}_college', '').strip()

            if not m_name:
                errors[f'member_{i}_name'] = f'Member {i+1} name is required.'
            if not m_email or not EMAIL_REGEX.match(m_email):
                errors[f'member_{i}_email'] = f'Member {i+1} requires a valid email.'
            elif m_email in member_emails:
                errors[f'member_{i}_email'] = f'Duplicate email ({m_email}) in team.'
            else:
                member_emails.add(m_email)

            m_phone_valid, m_clean_phone = cls.validate_phone(m_phone)
            if not m_phone_valid:
                errors[f'member_{i}_phone'] = f'Member {i+1} requires a valid Indian mobile number.'

            if not m_college:
                errors[f'member_{i}_college'] = f'Member {i+1} college is required.'

            additional_members.append({
                'name': m_name,
                'email': m_email,
                'phone': m_clean_phone,
                'college': m_college
            })

        if errors:
            return False, errors

        # 4. Atomic Database Transaction
        try:
            user = User(
                full_name=full_name,
                email=email,
                phone=clean_phone,
                role='team_leader',
                college=college,
                city=city,
                state=state,
                is_active=True,
                email_verified=False
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Get user.id

            reg_id = cls.generate_registration_id()
            team = Team(
                registration_id=reg_id,
                team_name=team_name,
                leader_user_id=user.id,
                team_size=team_size,
                registration_status='registered'
            )
            db.session.add(team)
            db.session.flush()  # Get team.id

            # Add leader as member #1
            leader_member = TeamMember(
                team_id=team.id,
                full_name=full_name,
                email=email,
                phone=clean_phone,
                college=college,
                is_leader=True
            )
            db.session.add(leader_member)

            # Add additional members
            for m in additional_members:
                member = TeamMember(
                    team_id=team.id,
                    full_name=m['name'],
                    email=m['email'],
                    phone=m['phone'],
                    college=m['college'],
                    is_leader=False
                )
                db.session.add(member)

            AuditLog.record(
                action='team_registered',
                entity_type='team',
                entity_id=team.registration_id,
                actor_id=user.id,
                metadata={'team_name': team.team_name, 'size': team_size}
            )

            db.session.commit()

            # Asynchronously / safely trigger email confirmation
            EmailService.send_registration_confirmation(user, team)

            return True, team

        except Exception as e:
            db.session.rollback()
            return False, {'general': f'Registration failed due to a database error: {str(e)}'}
