from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models.content import ProblemStatement, AuditLog
from app.models.team import Team, TeamMember
from app.services.settings_service import SettingsService

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    if current_user.is_admin and not current_user.team:
        return redirect(url_for('admin.overview'))

    team = current_user.team
    if not team:
        flash('No team found for your account. Please register your team.', 'warning')
        return redirect(url_for('registration.register'))

    problem = ProblemStatement.get_published()
    status_text, status_class = SettingsService.get_event_status()
    whatsapp_url = SettingsService.get_setting('whatsapp_group_url')
    unstop_reg_url = SettingsService.get_setting('unstop_opportunity_url')
    unstop_sub_url = SettingsService.get_setting('unstop_submission_url')
    submission_deadline_str = SettingsService.get_setting('submission_deadline')
    reg_deadline_str = SettingsService.get_setting('registration_end_date')

    can_submit = SettingsService.are_submissions_open(team)
    timeline = SettingsService.get_timeline()

    return render_template(
        'dashboard/index.html',
        team=team,
        problem=problem,
        timeline=timeline,
        event_status_text=status_text,
        event_status_class=status_class,
        whatsapp_url=whatsapp_url,
        unstop_reg_url=unstop_reg_url,
        unstop_sub_url=unstop_sub_url,
        submission_deadline=submission_deadline_str,
        reg_deadline=reg_deadline_str,
        can_submit=can_submit,
        submission=team.submission,
    )


@dashboard_bp.route('/dashboard/settings', methods=['GET', 'POST'])
@login_required
def settings():
    team = current_user.team
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'change_password':
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_new = request.form.get('confirm_new_password', '')

            if not current_user.check_password(old_password):
                flash('Current password is incorrect.', 'danger')
            elif len(new_password) < 8:
                flash('New password must be at least 8 characters.', 'danger')
            elif new_password != confirm_new:
                flash('New passwords do not match.', 'danger')
            else:
                current_user.set_password(new_password)
                AuditLog.record('password_changed', 'user', current_user.id, current_user.id)
                db.session.commit()
                flash('Your password has been changed successfully.', 'success')

        elif action == 'edit_team':
            if not team:
                flash('No team associated with this account.', 'danger')
            elif not team.allow_edit and not current_user.is_admin:
                flash('Team details editing is locked. Please request an administrator if you need corrections.', 'warning')
            else:
                # Update allowed fields
                new_team_name = request.form.get('team_name', '').strip()
                if new_team_name and new_team_name != team.team_name:
                    existing = Team.query.filter_by(team_name=new_team_name).first()
                    if existing:
                        flash('A team with that name already exists.', 'danger')
                        return redirect(url_for('dashboard.settings'))
                    team.team_name = new_team_name

                # Reset edit permission once used
                team.allow_edit = False
                AuditLog.record('team_details_updated', 'team', team.registration_id, current_user.id)
                db.session.commit()
                flash('Team details updated successfully.', 'success')

        return redirect(url_for('dashboard.settings'))

    return render_template('dashboard/settings.html', team=team)
