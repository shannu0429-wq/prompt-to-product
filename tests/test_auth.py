import pytest
from app import create_app
from app.extensions import db
from app.models.user import User


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_password_hashing(app):
    with app.app_context():
        user = User(
            full_name='Test User',
            email='test@example.com',
            phone='9876543210',
            college='Test College',
            city='Hyderabad',
            state='Telangana'
        )
        user.set_password('SecretPass123!')
        db.session.add(user)
        db.session.commit()

        # Plain text should not equal hash
        assert user.password_hash != 'SecretPass123!'
        # Correct verification
        assert user.check_password('SecretPass123!') is True
        # Incorrect verification
        assert user.check_password('WrongPass') is False


def test_user_roles(app):
    with app.app_context():
        leader = User(full_name='Leader', email='l@t.com', phone='1', college='c', city='c', state='s', role='team_leader')
        admin = User(full_name='Admin', email='a@t.com', phone='2', college='c', city='c', state='s', role='admin')
        super_admin = User(full_name='Super', email='sa@t.com', phone='3', college='c', city='c', state='s', role='super_admin')

        assert leader.is_admin is False
        assert leader.is_super_admin is False
        assert leader.is_team_leader is True

        assert admin.is_admin is True
        assert admin.is_super_admin is False

        assert super_admin.is_admin is True
        assert super_admin.is_super_admin is True
