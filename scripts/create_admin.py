import sys
import os
import getpass

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.content import AuditLog


def run_create_admin(full_name=None, email=None, password=None):
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("Prompt to Product – Secure Administrator Setup")
        print("=" * 60)

        if not full_name:
            full_name = input("Enter Super Admin Full Name [SSRS Super Admin]: ").strip()
            if not full_name:
                full_name = "SSRS Super Admin"

        if not email:
            email = input("Enter Super Admin Email: ").strip().lower()
            while not email or '@' not in email:
                print("Error: A valid email address is required.")
                email = input("Enter Super Admin Email: ").strip().lower()

        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"User with email '{email}' already exists.")
            promote = input(f"Promote '{email}' to super_admin role? (y/N): ").strip().lower()
            if promote == 'y':
                existing.role = 'super_admin'
                existing.is_active = True
                existing.email_verified = True
                db.session.commit()
                AuditLog.record('user_promoted_to_super_admin', 'user', existing.id)
                print(f"Success! {email} is now a super_admin.")
            return

        if not password:
            while True:
                password = getpass.getpass("Enter Super Admin Password (min 8 chars): ")
                if len(password) < 8:
                    print("Error: Password must be at least 8 characters long.")
                    continue
                confirm = getpass.getpass("Confirm Super Admin Password: ")
                if password != confirm:
                    print("Error: Passwords do not match.")
                    continue
                break

        admin_user = User(
            full_name=full_name,
            email=email,
            phone="9876543210",
            college="SSRS Group of Companies",
            city="Hyderabad",
            state="Telangana",
            role="super_admin",
            is_active=True,
            email_verified=True
        )
        admin_user.set_password(password)

        db.session.add(admin_user)
        db.session.flush()

        AuditLog.record('initial_super_admin_created', 'user', admin_user.id, actor_id=admin_user.id)
        db.session.commit()

        print("-" * 60)
        print(f"Super Admin successfully created!")
        print(f"Email: {email}")
        print(f"Role: super_admin")
        print("You can now log in at /admin/login")
        print("=" * 60)


if __name__ == '__main__':
    run_create_admin()
