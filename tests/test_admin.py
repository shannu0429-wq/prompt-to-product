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
        admin = User(
            full_name='SSRS Super Admin',
            email='admin@ssrsgc.com',
            phone='9876543210',
            college='SSRS Group of Companies',
            city='Hyderabad',
            state='Telangana',
            role='super_admin',
            is_active=True,
            email_verified=True
        )
        admin.set_password('AdminPassword2026!')
        db.session.add(admin)
        db.session.commit()
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
        # Ensure release date is past so get_published() can return it when published
        SettingsService.set_setting('problem_statement_release_date', '2020-01-01 00:00:00')

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

        # Test future release date hides problem statement from public
        SettingsService.set_setting('problem_statement_release_date', '2099-01-01 00:00:00')
        assert ProblemStatement.get_published(allow_unreleased=False) is None
        # But admin preview allows it
        assert ProblemStatement.get_published(allow_unreleased=True) is not None


def test_admin_problem_statement_add_update_remove(client, app):
    # Log in as admin
    client.post('/admin/login', data={
        'email': 'admin@ssrsgc.com',
        'password': 'AdminPassword2026!'
    }, follow_redirects=True)

    # 1. ADD a new problem statement as draft
    res = client.post('/admin/problem-statement', data={
        'action': 'save_draft',
        'title': 'Original AI Challenge',
        'description': 'Build an intelligent agent',
        'objectives': 'Deliver full prototype',
        'requirements': 'Flask + AI models',
        'guidelines': 'Standard rules',
        'evaluation_criteria': '60 marks rubric',
        'submission_instructions': 'Submit live URL'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        stmt_v1 = ProblemStatement.query.filter_by(title='Original AI Challenge').first()
        assert stmt_v1 is not None
        assert stmt_v1.version == 1
        assert stmt_v1.status == 'draft'
        v1_id = stmt_v1.id

    # 2. UPDATE existing problem statement and publish
    res = client.post('/admin/problem-statement', data={
        'action': 'publish',
        'statement_id': v1_id,
        'title': 'Updated AI Challenge v1',
        'description': 'Updated description',
        'objectives': 'Updated objectives',
        'requirements': 'Updated requirements',
        'guidelines': 'Updated guidelines',
        'evaluation_criteria': 'Updated criteria',
        'submission_instructions': 'Updated instructions'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        updated_stmt = ProblemStatement.query.get(v1_id)
        assert updated_stmt.title == 'Updated AI Challenge v1'
        assert updated_stmt.status == 'published'
        assert updated_stmt.published_at is not None

    # 3. ADD a second problem statement (v2)
    res = client.post('/admin/problem-statement', data={
        'action': 'save_draft',
        'title': 'AI Challenge Round 2',
        'description': 'Advanced problem statement',
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        stmt_v2 = ProblemStatement.query.filter_by(title='AI Challenge Round 2').first()
        assert stmt_v2 is not None
        assert stmt_v2.version == 2
        assert stmt_v2.status == 'draft'
        v2_id = stmt_v2.id

    # 4. PUBLISH existing v2, archiving v1
    res = client.post('/admin/problem-statement', data={
        'action': 'publish_existing',
        'statement_id': v2_id
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        stmt_v2_refreshed = ProblemStatement.query.get(v2_id)
        stmt_v1_refreshed = ProblemStatement.query.get(v1_id)
        assert stmt_v2_refreshed.status == 'published'
        assert stmt_v1_refreshed.status == 'archived'

    # 5. REMOVE / DELETE v1
    res = client.post('/admin/problem-statement', data={
        'action': 'delete',
        'statement_id': v1_id
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        deleted = ProblemStatement.query.get(v1_id)
        assert deleted is None
        # v2 still remains
        assert ProblemStatement.query.get(v2_id) is not None


def test_admin_schedule_time_access(client, app):
    # Log in as admin
    client.post('/admin/login', data={
        'email': 'admin@ssrsgc.com',
        'password': 'AdminPassword2026!'
    }, follow_redirects=True)

    # Update release and submission times from admin problem statement page
    res = client.post('/admin/problem-statement', data={
        'action': 'update_schedule',
        'problem_statement_release_date': '2026-11-05 10:00:00',
        'submission_start_date': '2026-11-05 12:00:00',
        'submission_deadline': '2026-11-20 23:59:59'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        assert SettingsService.get_setting('problem_statement_release_date') == '2026-11-05 10:00:00'
        assert SettingsService.get_setting('submission_start_date') == '2026-11-05 12:00:00'
        assert SettingsService.get_setting('submission_deadline') == '2026-11-20 23:59:59'
