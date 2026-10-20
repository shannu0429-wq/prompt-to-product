import hashlib
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.content import AuditLog, PasswordResetToken
from app.services.email_service import EmailService

auth_bp = Blueprint('auth', __name__)

# Simple in-memory rate limiter for login attempts (IP -> (count, lockout_until))
LOGIN_ATTEMPTS = {}


def check_rate_limit(ip_address, max_attempts=5, lockout_minutes=10):
    now = datetime.utcnow()
    record = LOGIN_ATTEMPTS.get(ip_address)
    if record:
        count, lockout_until = record
        if lockout_until and now < lockout_until:
            remaining = int((lockout_until - now).total_seconds() / 60) + 1
            return False, f"Too many failed login attempts. Please wait {remaining} minute(s)."
        if lockout_until and now >= lockout_until:
            LOGIN_ATTEMPTS[ip_address] = (1, None)
            return True, None
    return True, None


def record_failed_attempt(ip_address, max_attempts=5, lockout_minutes=10):
    now = datetime.utcnow()
    record = LOGIN_ATTEMPTS.get(ip_address)
    if record:
        count, _ = record
        new_count = count + 1
        if new_count >= max_attempts:
            lockout_until = now + timedelta(minutes=lockout_minutes)
            LOGIN_ATTEMPTS[ip_address] = (new_count, lockout_until)
        else:
            LOGIN_ATTEMPTS[ip_address] = (new_count, None)
    else:
        LOGIN_ATTEMPTS[ip_address] = (1, None)


def reset_failed_attempts(ip_address):
    LOGIN_ATTEMPTS.pop(ip_address, None)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.overview'))
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        ip = request.remote_addr or '127.0.0.1'
        allowed, reason = check_rate_limit(ip)
        if not allowed:
            flash(reason, 'danger')
            return render_template('auth/login.html')

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash('Please provide both email address and password.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            record_failed_attempt(ip)
            flash('Invalid email address or password.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Your account has been suspended or deactivated. Please contact the administrator.', 'danger')
            return render_template('auth/login.html')

        # Reset rate limit on success
        reset_failed_attempts(ip)

        # Update last login
        user.last_login_at = datetime.utcnow()
        db.session.commit()

        login_user(user, remember=remember)

        AuditLog.record(
            action='user_login',
            entity_type='user',
            entity_id=user.id,
            actor_id=user.id
        )

        flash(f'Welcome back, {user.full_name}!', 'success')
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        if user.is_admin:
            return redirect(url_for('admin.overview'))
        return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html')


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.overview'))

    if request.method == 'POST':
        ip = request.remote_addr or '127.0.0.1'
        allowed, reason = check_rate_limit(ip, max_attempts=5, lockout_minutes=15)
        if not allowed:
            flash(reason, 'danger')
            return render_template('auth/admin_login.html')

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password) or not user.is_admin:
            record_failed_attempt(ip, max_attempts=5, lockout_minutes=15)
            flash('Access denied. Invalid credentials or unauthorized account.', 'danger')
            return render_template('auth/admin_login.html')

        if not user.is_active:
            flash('This administrator account is currently suspended.', 'danger')
            return render_template('auth/admin_login.html')

        reset_failed_attempts(ip)
        user.last_login_at = datetime.utcnow()
        db.session.commit()

        login_user(user, remember=False)

        AuditLog.record(
            action='admin_login',
            entity_type='admin_user',
            entity_id=user.id,
            actor_id=user.id
        )

        flash(f'Logged in as Administrator ({user.role.title()}).', 'success')
        return redirect(url_for('admin.overview'))

    return render_template('auth/admin_login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    AuditLog.record(
        action='user_logout',
        entity_type='user',
        entity_id=current_user.id,
        actor_id=current_user.id
    )
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('public.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash('Please enter your registered email address.', 'danger')
            return render_template('auth/forgot_password.html')

        user = User.query.filter_by(email=email).first()
        if user and user.is_active:
            # Generate secure token
            raw_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
            expires_at = datetime.utcnow() + timedelta(hours=1)

            reset_record = PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at
            )
            db.session.add(reset_record)
            db.session.commit()

            base_url = current_app.config.get('PUBLIC_BASE_URL', 'http://127.0.0.1:5000').rstrip('/')
            reset_url = f"{base_url}/reset-password/{raw_token}"

            EmailService.send_password_reset_email(user, reset_url)

        # Generic safe response to prevent account enumeration
        flash('If that email is registered in our system, a password reset link has been dispatched.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    reset_record = PasswordResetToken.query.filter_by(token_hash=token_hash, used_at=None).first()

    if not reset_record or reset_record.expires_at < datetime.utcnow():
        flash('This password reset link is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not password or len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        user = reset_record.user
        user.set_password(password)
        reset_record.used_at = datetime.utcnow()

        AuditLog.record(
            action='password_reset_completed',
            entity_type='user',
            entity_id=user.id,
            actor_id=user.id
        )

        db.session.commit()
        flash('Your password has been successfully reset. Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)
