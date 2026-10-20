from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.submission_service import SubmissionService
from app.services.settings_service import SettingsService
from app.models.submission import Submission

submissions_bp = Blueprint('submissions', __name__)


@submissions_bp.route('/dashboard/submit', methods=['GET', 'POST'])
@login_required
def submit():
    team = current_user.team
    if not team:
        flash('You must register a team before submitting a project.', 'danger')
        return redirect(url_for('registration.register'))

    existing_submission = team.submission
    can_submit, reason = SubmissionService.can_submit_or_edit(team, is_edit=bool(existing_submission))
    unstop_sub_url = SettingsService.get_setting('unstop_submission_url')
    sub_deadline = SettingsService.get_setting('submission_deadline')

    if request.method == 'POST':
        website_url = request.form.get('website_url', '').strip()
        project_description = request.form.get('project_description', '').strip()

        if existing_submission:
            # Editing an existing submission
            success, result = SubmissionService.edit_submission(
                existing_submission,
                current_user,
                website_url,
                project_description
            )
        else:
            # New submission
            success, result = SubmissionService.submit_project(
                team,
                current_user,
                website_url,
                project_description
            )

        if not success:
            flash(result, 'danger')
            return render_template(
                'dashboard/submit.html',
                team=team,
                submission=existing_submission,
                can_submit=can_submit,
                reason=reason,
                unstop_sub_url=unstop_sub_url,
                sub_deadline=sub_deadline
            )

        flash('Your project website link has been successfully recorded!', 'success')
        return redirect(url_for('submissions.confirmation', sub_id=result.submission_id))

    return render_template(
        'dashboard/submit.html',
        team=team,
        submission=existing_submission,
        can_submit=can_submit,
        reason=reason,
        unstop_sub_url=unstop_sub_url,
        sub_deadline=sub_deadline
    )


@submissions_bp.route('/dashboard/submit/confirmation/<sub_id>')
@login_required
def confirmation(sub_id):
    submission = Submission.query.filter_by(submission_id=sub_id).first_or_404()
    # Ensure team owner or admin access
    if submission.team.leader_user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized access to submission details.', 'danger')
        return redirect(url_for('dashboard.index'))

    unstop_sub_url = SettingsService.get_setting('unstop_submission_url')
    confirmation_text = SettingsService.get_setting(
        'submission_confirmation_text',
        'Your project has been recorded in our database. Note that you must also submit on Unstop to complete your hackathon participation!'
    )

    return render_template(
        'dashboard/submit_confirmation.html',
        submission=submission,
        team=submission.team,
        unstop_sub_url=unstop_sub_url,
        confirmation_text=confirmation_text
    )
