import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.team import Team, TeamMember
from app.models.submission import Submission
from app.services.submission_service import SubmissionService
from app.services.registration_service import RegistrationService
from app.services.settings_service import SettingsService


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        SettingsService.seed_defaults()
        yield app
        db.session.remove()
        db.drop_all()


def test_url_validation():
    # Valid URLs
    valid, res = SubmissionService.validate_website_url('https://my-app.vercel.app')
    assert valid is True
    assert res == 'https://my-app.vercel.app'

    valid, res = SubmissionService.validate_website_url('http://deployed-project.com')
    assert valid is True

    # Invalid schemes
    valid, res = SubmissionService.validate_website_url('ftp://fileserver.com')
    assert valid is False

    valid, res = SubmissionService.validate_website_url('file:///C:/my-code.zip')
    assert valid is False

    valid, res = SubmissionService.validate_website_url('javascript:alert(1)')
    assert valid is False

    valid, res = SubmissionService.validate_website_url('')
    assert valid is False


def test_submission_lifecycle(app):
    with app.app_context():
        # Register a team first
        form_data = {
            'team_name': 'CodeCraft',
            'team_size': '1',
            'leader_name': 'Neha Verma',
            'leader_email': 'neha@test.com',
            'leader_phone': '9876543210',
            'leader_college': 'NIT Trichy',
            'leader_city': 'Trichy',
            'leader_state': 'Tamil Nadu',
            'leader_password': 'Password123!',
            'leader_confirm_password': 'Password123!',
        }
        success, team = RegistrationService.register_team(form_data)
        assert success is True

        # Initial Submission
        success, sub = SubmissionService.submit_project(
            team=team,
            user=team.leader,
            website_url='https://codecraft.vercel.app',
            project_description='AI-powered analytics tool'
        )
        assert success is True
        assert sub.submission_id.startswith('SUB-2026-')
        assert sub.website_url == 'https://codecraft.vercel.app'
        assert len(sub.history) == 1

        # Attempt duplicate submission when resubmission disabled
        success, msg = SubmissionService.submit_project(
            team=team,
            user=team.leader,
            website_url='https://codecraft-v2.vercel.app'
        )
        assert success is False
        assert 'already submitted' in msg.lower()
