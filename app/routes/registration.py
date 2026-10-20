from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, current_user
from app.services.registration_service import RegistrationService
from app.services.settings_service import SettingsService
from app.models.team import Team

registration_bp = Blueprint('registration', __name__)


@registration_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('You are already logged in. View your team dashboard below.', 'info')
        return redirect(url_for('dashboard.index'))

    # Check if registration is open
    if not SettingsService.is_registration_open():
        flash('Team registrations are currently closed.', 'warning')
        return render_template('auth/registration_closed.html')

    if request.method == 'POST':
        form_data = request.form.to_dict()
        success, result = RegistrationService.register_team(form_data)

        if not success:
            for field, err in result.items():
                flash(err, 'danger')
            return render_template('auth/register.html', form_data=form_data)

        team = result
        # Auto-login leader
        login_user(team.leader)
        flash('Registration completed successfully! Welcome to Prompt to Product.', 'success')
        return redirect(url_for('registration.success', reg_id=team.registration_id))

    return render_template('auth/register.html', form_data={})


@registration_bp.route('/register/success/<reg_id>')
def success(reg_id):
    team = Team.query.filter_by(registration_id=reg_id).first_or_404()
    whatsapp_url = SettingsService.get_setting('whatsapp_group_url')
    unstop_url = SettingsService.get_setting('unstop_opportunity_url')

    return render_template(
        'auth/register_success.html',
        team=team,
        whatsapp_url=whatsapp_url,
        unstop_url=unstop_url
    )
