import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.content import ProblemStatement, SiteSetting
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


@pytest.fixture
def client(app):
    return app.test_client()


def test_admin_route_protection(client):
    # Unauthenticated access to /admin must redirect to admin login
    res = client.get('/admin/', follow_redirects=False)
    assert res.status_code == 302
    assert '/admin/login' in res.headers['Location']


def test_site_settings_service(app):
    with app.app_context():
        val = SettingsService.get_setting('event_title')
        assert 'Prompt to Product' in val

        SettingsService.set_setting('event_title', 'Updated Hackathon Title')
        new_val = SettingsService.get_setting('event_title')
        assert new_val == 'Updated Hackathon Title'


def test_problem_statement_lifecycle(app):
    with app.app_context():
        ps = ProblemStatement(
            title='Test Problem Statement',
            description='Test Description',
            status='draft',
            version=1
        )
        db.session.add(ps)
        db.session.commit()

        # Should not be returned by get_published() while draft
        assert ProblemStatement.get_published() is None

        # Publish
        ps.status = 'published'
        db.session.commit()

        published = ProblemStatement.get_published()
        assert published is not None
        assert published.title == 'Test Problem Statement'
