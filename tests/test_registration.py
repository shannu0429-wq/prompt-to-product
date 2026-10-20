import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.team import Team, TeamMember
from app.services.registration_service import RegistrationService


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_phone_validation():
    valid, p = RegistrationService.validate_phone('9876543210')
    assert valid is True
    assert p == '9876543210'

    valid, p = RegistrationService.validate_phone('+91 9876543210')
    assert valid is True
    assert p == '9876543210'

    valid, p = RegistrationService.validate_phone('12345')
    assert valid is False


def test_register_team_success(app):
    with app.app_context():
        form_data = {
            'team_name': 'Alpha Builders',
            'team_size': '2',
            'leader_name': 'Rahul Sharma',
            'leader_email': 'rahul@test.com',
            'leader_phone': '9876543210',
            'leader_college': 'IIT Delhi',
            'leader_city': 'New Delhi',
            'leader_state': 'Delhi',
            'leader_password': 'Password123!',
            'leader_confirm_password': 'Password123!',
            'member_1_name': 'Priya Singh',
            'member_1_email': 'priya@test.com',
            'member_1_phone': '8765432109',
            'member_1_college': 'IIT Delhi',
        }

        success, result = RegistrationService.register_team(form_data)
        assert success is True
        assert isinstance(result, Team)
        assert result.team_name == 'Alpha Builders'
        assert result.registration_id.startswith('P2P-2026-')
        assert len(result.members) == 2

        # Verify in DB
        team_in_db = Team.query.filter_by(team_name='Alpha Builders').first()
        assert team_in_db is not None
        assert team_in_db.leader.email == 'rahul@test.com'


def test_register_duplicate_prevention(app):
    with app.app_context():
        form_data = {
            'team_name': 'Solo Innovator',
            'team_size': '1',
            'leader_name': 'Aman Gupta',
            'leader_email': 'aman@test.com',
            'leader_phone': '9988776655',
            'leader_college': 'BITS Pilani',
            'leader_city': 'Hyderabad',
            'leader_state': 'Telangana',
            'leader_password': 'Password123!',
            'leader_confirm_password': 'Password123!',
        }

        success, _ = RegistrationService.register_team(form_data)
        assert success is True

        # Duplicate email
        dup_email_data = dict(form_data)
        dup_email_data['team_name'] = 'Another Team'
        success, errors = RegistrationService.register_team(dup_email_data)
        assert success is False
        assert 'leader_email' in errors

        # Duplicate team name
        dup_name_data = dict(form_data)
        dup_name_data['leader_email'] = 'new_email@test.com'
        success, errors = RegistrationService.register_team(dup_name_data)
        assert success is False
        assert 'team_name' in errors
