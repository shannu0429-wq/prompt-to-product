import re
import pytest
from app import create_app
from app.extensions import db
from app.models.content import SiteSetting, ProblemStatement
from app.models.user import User


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        # Create Super Admin
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


def test_public_pages(client):
    pages = ['/', '/about', '/problem-statement', '/rules', '/contact', '/login', '/register', '/admin/login']
    for p in pages:
        res = client.get(p)
        assert res.status_code == 200, f"Page {p} returned status {res.status_code}"


def test_super_admin_authenticated_flows(client):
    # Log in as Super Admin
    login_res = client.post('/admin/login', data={
        'email': 'admin@ssrsgc.com',
        'password': 'AdminPassword2026!'
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b'Dashboard Overview' in login_res.data

    # Test all 16 Admin panels
    admin_routes = [
        '/admin/',
        '/admin/editor',
        '/admin/branding',
        '/admin/event-settings',
        '/admin/problem-statement',
        '/admin/registrations',
        '/admin/submissions',
        '/admin/evaluations',
        '/admin/results',
        '/admin/announcements',
        '/admin/faqs',
        '/admin/email',
        '/admin/links',
        '/admin/users',
        '/admin/audit-logs',
        '/admin/system-status',
    ]

    for route in admin_routes:
        res = client.get(route)
        assert res.status_code == 200, f"Admin route {route} failed with {res.status_code}"
