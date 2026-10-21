import csv
import io
import os
import secrets
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, request, flash, redirect, url_for, Response, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.user import User
from app.models.team import Team, TeamMember
from app.models.submission import Submission, SubmissionHistory
from app.models.content import (
    ProblemStatement,
    Announcement,
    FAQ,
    SiteSetting,
    AuditLog,
)
from app.models.evaluation import Evaluation, Result
from app.services.settings_service import SettingsService, DEFAULT_SETTINGS
from app.services.email_service import EmailService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.admin_login', next=request.path))
        if not current_user.is_admin:
            flash('Access restricted. Administrator privileges required.', 'danger')
            return redirect(url_for('auth.admin_login'))
        if not current_user.is_active:
            flash('Your administrator account is suspended.', 'danger')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.admin_login', next=request.path))
        if not current_user.is_super_admin:
            flash('This action requires Super Admin authority.', 'danger')
            return redirect(url_for('admin.overview'))
        if not current_user.is_active:
            flash('Your administrator account is suspended.', 'danger')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# 1. OVERVIEW
@admin_bp.route('/')
@admin_required
def overview():
    total_leaders = User.query.filter_by(role='team_leader').count()
    total_teams = Team.query.count()
    total_members = TeamMember.query.count()
    total_submissions = Submission.query.count()
    pending_submissions = Submission.query.filter_by(status='submitted').count()
    shortlisted_submissions = Submission.query.filter_by(status='shortlisted').count()
    verified_emails = User.query.filter_by(email_verified=True).count()
    total_statements = ProblemStatement.query.count()
    published_statements = ProblemStatement.query.filter_by(status='published').count()

    recent_teams = Team.query.order_by(Team.created_at.desc()).limit(8).all()
    recent_submissions = Submission.query.order_by(Submission.submitted_at.desc()).limit(6).all()
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()

    status_text, status_class = SettingsService.get_event_status()
    published_problem = ProblemStatement.get_published()

    return render_template(
        'admin/overview.html',
        total_leaders=total_leaders,
        total_teams=total_teams,
        total_members=total_members,
        total_submissions=total_submissions,
        pending_submissions=pending_submissions,
        shortlisted_submissions=shortlisted_submissions,
        verified_emails=verified_emails,
        total_statements=total_statements,
        published_statements=published_statements,
        recent_teams=recent_teams,
        recent_submissions=recent_submissions,
        recent_logs=recent_logs,
        event_status_text=status_text,
        event_status_class=status_class,
        published_problem=published_problem,
    )


# 2. WEBSITE EDITOR
@admin_bp.route('/editor', methods=['GET', 'POST'])
@admin_required
def editor():
    if request.method == 'POST':
        keys = [
            'event_title', 'event_subtitle', 'event_description',
            'organizer_name', 'organizer_tagline', 'contact_email', 'contact_phone',
            'submission_confirmation_text', 'announcement_banner'
        ]
        for k in keys:
            if k in request.form:
                SettingsService.set_setting(k, request.form.get(k, '').strip())

        AuditLog.record('website_content_updated', 'site_settings', actor_id=current_user.id)
        flash('Website content and copy updated successfully.', 'success')
        return redirect(url_for('admin.editor'))

    settings = SettingsService.get_all_settings()
    return render_template('admin/editor.html', settings=settings)


# 3. LOGO AND BRANDING
@admin_bp.route('/branding', methods=['GET', 'POST'])
@admin_required
def branding():
    static_images_dir = os.path.join(current_app.root_path, 'static', 'images')
    
    # Scan available logos
    available_logos = []
    if os.path.exists(static_images_dir):
        for f in os.listdir(static_images_dir):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.webp')):
                full_p = os.path.join(static_images_dir, f)
                rel_url = f"/static/images/{f}"
                available_logos.append({
                    'filename': f,
                    'url': rel_url,
                    'size_bytes': os.path.getsize(full_p)
                })

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'select_logo':
            chosen_logo = request.form.get('selected_logo')
            if chosen_logo:
                SettingsService.set_setting('active_logo_path', chosen_logo)
                AuditLog.record('active_logo_changed', 'branding', actor_id=current_user.id, metadata={'path': chosen_logo})
                flash('Active logo updated successfully.', 'success')

        elif action == 'upload_logo':
            if 'logo_file' not in request.files:
                flash('No file selected.', 'danger')
            else:
                file = request.files['logo_file']
                if file and file.filename:
                    ext = file.filename.rsplit('.', 1)[-1].lower()
                    if ext not in current_app.config['ALLOWED_IMAGE_EXTENSIONS']:
                        flash('Invalid image format. Allowed: PNG, JPG, JPEG, SVG, WEBP.', 'danger')
                    else:
                        safe_name = f"uploaded_logo_{secrets.token_hex(4)}.{ext}"
                        target_path = os.path.join(static_images_dir, safe_name)
                        file.save(target_path)
                        logo_url = f"/static/images/{safe_name}"
                        SettingsService.set_setting('active_logo_path', logo_url)
                        AuditLog.record('custom_logo_uploaded', 'branding', actor_id=current_user.id, metadata={'filename': safe_name})
                        flash('New logo uploaded and set as active.', 'success')
                        return redirect(url_for('admin.branding'))

        return redirect(url_for('admin.branding'))

    current_logo = SettingsService.get_active_logo()
    return render_template(
        'admin/branding.html',
        available_logos=available_logos,
        current_logo=current_logo
    )


# 4. EVENT SETTINGS
@admin_bp.route('/event-settings', methods=['GET', 'POST'])
@admin_required
def event_settings():
    if request.method == 'POST':
        SettingsService.set_setting('registration_start_date', request.form.get('registration_start_date', ''))
        SettingsService.set_setting('registration_end_date', request.form.get('registration_end_date', ''))
        SettingsService.set_setting('problem_statement_release_date', request.form.get('problem_statement_release_date', ''))
        SettingsService.set_setting('submission_start_date', request.form.get('submission_start_date', ''))
        SettingsService.set_setting('submission_deadline', request.form.get('submission_deadline', ''))
        
        SettingsService.set_setting('submissions_open', 'true' if request.form.get('submissions_open') else 'false')
        SettingsService.set_setting('registration_open', 'true' if request.form.get('registration_open') else 'false')
        SettingsService.set_setting('allow_resubmission', 'true' if request.form.get('allow_resubmission') else 'false')
        SettingsService.set_setting('allow_post_submit_edits', 'true' if request.form.get('allow_post_submit_edits') else 'false')
        SettingsService.set_setting('event_status_override', request.form.get('event_status_override', 'auto'))
        SettingsService.set_setting('participation_certificates_enabled', 'true' if request.form.get('participation_certificates_enabled') else 'false')

        AuditLog.record('event_settings_updated', 'settings', actor_id=current_user.id)
        flash('Event dates and operational settings updated.', 'success')
        return redirect(url_for('admin.event_settings'))

    settings = SettingsService.get_all_settings()
    return render_template('admin/event_settings.html', settings=settings)


# 5. PROBLEM STATEMENT & SCHEDULE TIMING MANAGEMENT
@admin_bp.route('/problem-statement', methods=['GET', 'POST'])
@admin_required
def problem_statement():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action in ['save_draft', 'publish']:
            ps_id = request.form.get('statement_id')
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            objectives = request.form.get('objectives', '').strip()
            requirements = request.form.get('requirements', '').strip()
            guidelines = request.form.get('guidelines', '').strip()
            evaluation_criteria = request.form.get('evaluation_criteria', '').strip()
            submission_instructions = request.form.get('submission_instructions', '').strip()

            if not title or not description:
                flash('Problem title and description are required.', 'danger')
                return redirect(url_for('admin.problem_statement'))

            if ps_id:
                statement = ProblemStatement.query.get(ps_id)
                if not statement:
                    flash('Selected problem statement not found.', 'danger')
                    return redirect(url_for('admin.problem_statement'))
            else:
                statement = ProblemStatement(created_by=current_user.id)
                # Next version
                last_stmt = ProblemStatement.query.order_by(ProblemStatement.version.desc()).first()
                statement.version = (last_stmt.version + 1) if last_stmt else 1
                db.session.add(statement)

            statement.title = title
            statement.description = description
            statement.objectives = objectives
            statement.requirements = requirements
            statement.guidelines = guidelines
            statement.evaluation_criteria = evaluation_criteria
            statement.submission_instructions = submission_instructions
            statement.updated_at = datetime.utcnow()

            if action == 'publish':
                # Archive all other published versions so only 1 is active
                ProblemStatement.query.filter(
                    ProblemStatement.id != statement.id,
                    ProblemStatement.status == 'published'
                ).update({'status': 'archived'})
                statement.status = 'published'
                statement.published_at = datetime.utcnow()
                AuditLog.record('problem_statement_published', 'problem_statement', statement.id, current_user.id, {'version': statement.version})
                flash(f'Problem Statement v{statement.version} ("{statement.title}") published to website successfully!', 'success')
            else:
                statement.status = 'draft'
                AuditLog.record('problem_statement_draft_saved', 'problem_statement', statement.id, current_user.id, {'version': statement.version})
                flash(f'Problem Statement v{statement.version} saved as draft.', 'info')

            db.session.commit()
            return redirect(url_for('admin.problem_statement'))

        elif action == 'publish_existing':
            ps_id = request.form.get('statement_id')
            stmt = ProblemStatement.query.get_or_404(ps_id)
            ProblemStatement.query.filter(
                ProblemStatement.id != stmt.id,
                ProblemStatement.status == 'published'
            ).update({'status': 'archived'})
            stmt.status = 'published'
            stmt.published_at = datetime.utcnow()
            db.session.commit()
            AuditLog.record('problem_statement_published', 'problem_statement', stmt.id, current_user.id, {'version': stmt.version})
            flash(f'Problem Statement v{stmt.version} ("{stmt.title}") is now published as the live version!', 'success')
            return redirect(url_for('admin.problem_statement'))

        elif action == 'unpublish':
            ps_id = request.form.get('statement_id')
            stmt = ProblemStatement.query.get_or_404(ps_id)
            stmt.status = 'draft'
            db.session.commit()
            AuditLog.record('problem_statement_unpublished', 'problem_statement', stmt.id, current_user.id, {'version': stmt.version})
            flash(f'Problem Statement v{stmt.version} has been set back to draft.', 'warning')
            return redirect(url_for('admin.problem_statement'))

        elif action == 'delete':
            ps_id = request.form.get('statement_id')
            stmt = ProblemStatement.query.get_or_404(ps_id)
            v = stmt.version
            t = stmt.title
            db.session.delete(stmt)
            db.session.commit()
            AuditLog.record('problem_statement_deleted', 'problem_statement', ps_id, current_user.id, {'version': v, 'title': t})
            flash(f'Problem Statement v{v} ("{t}") was permanently removed.', 'success')
            return redirect(url_for('admin.problem_statement'))

        elif action == 'update_schedule':
            rel_date = request.form.get('problem_statement_release_date', '').strip()
            sub_start = request.form.get('submission_start_date', '').strip()
            sub_deadline = request.form.get('submission_deadline', '').strip()

            if rel_date:
                SettingsService.set_setting('problem_statement_release_date', rel_date)
            if sub_start:
                SettingsService.set_setting('submission_start_date', sub_start)
            if sub_deadline:
                SettingsService.set_setting('submission_deadline', sub_deadline)

            AuditLog.record('schedule_times_updated', 'site_settings', 0, current_user.id, {
                'problem_statement_release_date': rel_date,
                'submission_start_date': sub_start,
                'submission_deadline': sub_deadline
            })
            flash('Event schedule and release times have been updated successfully!', 'success')
            return redirect(url_for('admin.problem_statement'))

    edit_id = request.args.get('edit_id')
    mode = request.args.get('mode')  # 'new'
    statements = ProblemStatement.query.order_by(ProblemStatement.version.desc()).all()
    current_published = ProblemStatement.query.filter_by(status='published').order_by(ProblemStatement.version.desc()).first()

    selected_stmt = None
    if mode == 'new':
        selected_stmt = None
    elif edit_id:
        selected_stmt = ProblemStatement.query.get(edit_id)
    else:
        selected_stmt = current_published or (statements[0] if statements else None)

    # Next version calculation
    max_version = db.session.query(db.func.max(ProblemStatement.version)).scalar() or 0
    next_version = max_version + 1

    return render_template(
        'admin/problem_statement.html',
        statements=statements,
        current_published=current_published,
        selected_stmt=selected_stmt,
        mode=mode,
        edit_id=edit_id,
        next_version=next_version
    )


# 6. REGISTRATIONS & TEAMS
@admin_bp.route('/registrations')
@admin_required
def registrations():
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Team.query.join(User, Team.leader_user_id == User.id)

    if search_query:
        query = query.filter(
            db.or_(
                Team.team_name.ilike(f"%{search_query}%"),
                Team.registration_id.ilike(f"%{search_query}%"),
                User.full_name.ilike(f"%{search_query}%"),
                User.email.ilike(f"%{search_query}%"),
                User.phone.ilike(f"%{search_query}%")
            )
        )

    if status_filter:
        query = query.filter(Team.registration_status == status_filter)

    pagination = query.order_by(Team.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    teams = pagination.items

    return render_template(
        'admin/registrations.html',
        teams=teams,
        pagination=pagination,
        search_query=search_query,
        status_filter=status_filter
    )


@admin_bp.route('/teams/<int:team_id>', methods=['GET', 'POST'])
@admin_required
def team_detail(team_id):
    team = Team.query.get_or_404(team_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_status':
            new_status = request.form.get('registration_status')
            if new_status in ['registered', 'verified', 'under_review', 'suspended']:
                team.registration_status = new_status
                AuditLog.record('team_status_updated', 'team', team.registration_id, current_user.id, {'status': new_status})
                flash(f'Status changed to {new_status}.', 'success')

        elif action == 'toggle_edit_permission':
            team.allow_edit = not team.allow_edit
            AuditLog.record('team_edit_permission_toggled', 'team', team.registration_id, current_user.id, {'allow_edit': team.allow_edit})
            flash(f"Team edit permission {'granted' if team.allow_edit else 'revoked'}.", 'info')

        elif action == 'toggle_resubmit_permission':
            team.allow_resubmit = not team.allow_resubmit
            AuditLog.record('team_resubmit_permission_toggled', 'team', team.registration_id, current_user.id, {'allow_resubmit': team.allow_resubmit})
            flash(f"Team resubmission permission {'granted' if team.allow_resubmit else 'revoked'}.", 'info')

        elif action == 'save_notes':
            team.internal_notes = request.form.get('internal_notes', '')
            AuditLog.record('team_notes_updated', 'team', team.registration_id, current_user.id)
            flash('Internal administrator notes saved.', 'success')

        elif action == 'edit_team_info':
            new_name = request.form.get('team_name', '').strip()
            if new_name and new_name != team.team_name:
                existing = Team.query.filter_by(team_name=new_name).first()
                if existing:
                    flash('That team name is already in use.', 'danger')
                    return redirect(url_for('admin.team_detail', team_id=team.id))
                team.team_name = new_name

            # Update leader info
            team.leader.full_name = request.form.get('leader_name', team.leader.full_name).strip()
            team.leader.phone = request.form.get('leader_phone', team.leader.phone).strip()
            team.leader.college = request.form.get('leader_college', team.leader.college).strip()
            AuditLog.record('team_info_corrected_by_admin', 'team', team.registration_id, current_user.id)
            flash('Team details updated.', 'success')

        elif action == 'delete_team' and current_user.is_super_admin:
            reg_id = team.registration_id
            db.session.delete(team)
            AuditLog.record('team_deleted_permanently', 'team', reg_id, current_user.id)
            db.session.commit()
            flash(f'Team {reg_id} deleted permanently.', 'warning')
            return redirect(url_for('admin.registrations'))

        db.session.commit()
        return redirect(url_for('admin.team_detail', team_id=team.id))

    return render_template('admin/team_detail.html', team=team)


@admin_bp.route('/registrations/export')
@admin_required
def export_registrations():
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Team ID', 'Team Name', 'Team Size', 'Status',
        'Leader Name', 'Leader Email', 'Leader Phone', 'College', 'City', 'State',
        'Member 2 Name', 'Member 2 Email', 'Member 2 Phone',
        'Member 3 Name', 'Member 3 Email', 'Member 3 Phone',
        'Member 4 Name', 'Member 4 Email', 'Member 4 Phone',
        'Registered At', 'Has Submitted', 'Submission URL'
    ])

    teams = Team.query.order_by(Team.created_at.asc()).all()
    for t in teams:
        members = [m for m in t.members if not m.is_leader]
        row = [
            t.registration_id,
            t.team_name,
            t.team_size,
            t.registration_status,
            t.leader.full_name,
            t.leader.email,
            t.leader.phone,
            t.leader.college,
            t.leader.city,
            t.leader.state,
        ]
        # Member slots 2, 3, 4
        for i in range(3):
            if i < len(members):
                m = members[i]
                row.extend([m.full_name, m.email, m.phone])
            else:
                row.extend(['', '', ''])

        row.append(t.created_at.strftime('%Y-%m-%d %H:%M:%S'))
        row.append('Yes' if t.submission else 'No')
        row.append(t.submission.website_url if t.submission else '')

        writer.writerow(row)

    AuditLog.record('registrations_exported_csv', 'team', actor_id=current_user.id)

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=PromptToProduct_Registrations.csv'
    return response


# 7. SUBMISSIONS MANAGEMENT
@admin_bp.route('/submissions', methods=['GET', 'POST'])
@admin_required
def submissions():
    if request.method == 'POST':
        action = request.form.get('action')
        sub_id = request.form.get('submission_id')
        sub = Submission.query.get_or_404(sub_id)

        if action == 'update_status':
            new_status = request.form.get('status')
            if new_status in ['submitted', 'under_review', 'shortlisted', 'rejected']:
                sub.status = new_status
                AuditLog.record('submission_status_changed', 'submission', sub.submission_id, current_user.id, {'status': new_status})
                flash(f'Submission {sub.submission_id} marked as {new_status}.', 'success')

        elif action == 'edit_url':
            new_url = request.form.get('website_url', '').strip()
            if new_url.startswith(('http://', 'https://')):
                sub.website_url = new_url
                history = SubmissionHistory(
                    submission_id=sub.id,
                    website_url=new_url,
                    project_description=sub.project_description,
                    changed_by=current_user.id,
                    change_type='admin_edit',
                    changed_at=datetime.utcnow()
                )
                db.session.add(history)
                AuditLog.record('submission_url_edited_by_admin', 'submission', sub.submission_id, current_user.id, {'new_url': new_url})
                flash('Website link updated with audit trail.', 'success')
            else:
                flash('Invalid URL format.', 'danger')

        db.session.commit()
        return redirect(url_for('admin.submissions'))

    search = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Submission.query.join(Team, Submission.team_id == Team.id)
    if search:
        query = query.filter(
            db.or_(
                Submission.submission_id.ilike(f"%{search}%"),
                Team.team_name.ilike(f"%{search}%"),
                Team.registration_id.ilike(f"%{search}%"),
                Submission.website_url.ilike(f"%{search}%")
            )
        )
    if status_filter:
        query = query.filter(Submission.status == status_filter)

    pagination = query.order_by(Submission.submitted_at.desc()).paginate(page=page, per_page=15, error_out=False)
    subs = pagination.items

    return render_template(
        'admin/submissions.html',
        submissions=subs,
        pagination=pagination,
        search=search,
        status_filter=status_filter
    )


@admin_bp.route('/submissions/export')
@admin_required
def export_submissions():
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Submission ID', 'Team ID', 'Team Name', 'Leader Name', 'Leader Email',
        'Website URL', 'Project Description', 'Status', 'Submitted At',
        'Evaluation Total (/60)', 'Rank'
    ])

    subs = Submission.query.order_by(Submission.submitted_at.asc()).all()
    for s in subs:
        score = s.evaluation.total_score if s.evaluation else ''
        rank = s.team.result.rank if s.team.result else ''
        writer.writerow([
            s.submission_id,
            s.team.registration_id,
            s.team.team_name,
            s.team.leader.full_name,
            s.team.leader.email,
            s.website_url,
            s.project_description or '',
            s.status,
            s.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            score,
            rank
        ])

    AuditLog.record('submissions_exported_csv', 'submission', actor_id=current_user.id)

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=PromptToProduct_Submissions.csv'
    return response


# 8. EVALUATION AND RANKINGS
@admin_bp.route('/evaluations', methods=['GET', 'POST'])
@admin_required
def evaluations():
    if request.method == 'POST':
        action = request.form.get('action')

        if action in ['save_score', 'finalize_score']:
            sub_id = request.form.get('submission_id')
            sub = Submission.query.get_or_404(sub_id)

            eval_record = sub.evaluation or Evaluation(submission_id=sub.id, evaluator_id=current_user.id)
            if not sub.evaluation:
                db.session.add(eval_record)

            try:
                eval_record.score_functionality = max(0.0, min(10.0, float(request.form.get('score_functionality', 0))))
                eval_record.score_innovation = max(0.0, min(10.0, float(request.form.get('score_innovation', 0))))
                eval_record.score_prompt_engineering = max(0.0, min(10.0, float(request.form.get('score_prompt_engineering', 0))))
                eval_record.score_ui_ux = max(0.0, min(10.0, float(request.form.get('score_ui_ux', 0))))
                eval_record.score_real_world_impact = max(0.0, min(10.0, float(request.form.get('score_real_world_impact', 0))))
                eval_record.score_code_quality = max(0.0, min(10.0, float(request.form.get('score_code_quality', 0))))
                eval_record.comments = request.form.get('comments', '')
                eval_record.calculate_total()
                eval_record.is_finalized = (action == 'finalize_score')
                eval_record.updated_at = datetime.utcnow()

                AuditLog.record(
                    'evaluation_saved',
                    'evaluation',
                    sub.submission_id,
                    current_user.id,
                    {'total': eval_record.total_score, 'finalized': eval_record.is_finalized}
                )

                db.session.commit()
                flash(f"Score for {sub.team.team_name} saved: {eval_record.total_score}/60.", 'success')
            except ValueError:
                flash('Please enter valid numerical scores between 0 and 10.', 'danger')

        return redirect(url_for('admin.evaluations'))

    submissions = Submission.query.all()
    # Rank finalized submissions
    evaluated_subs = [s for s in submissions if s.evaluation and s.evaluation.is_finalized]
    evaluated_subs.sort(key=lambda s: s.evaluation.total_score, reverse=True)

    return render_template(
        'admin/evaluations.html',
        submissions=submissions,
        ranked_subs=evaluated_subs
    )


# 9. RESULTS AND WINNERS
@admin_bp.route('/results', methods=['GET', 'POST'])
@admin_required
def results():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'calculate_rankings':
            # Recalculate rankings from finalized evaluations
            evals = Evaluation.query.filter_by(is_finalized=True).order_by(Evaluation.total_score.desc()).all()
            # Clear previous results
            Result.query.delete()

            rank = 1
            for ev in evals:
                team = ev.submission.team
                res = Result(
                    team_id=team.id,
                    rank=rank,
                    is_top_three=(rank <= 3),
                    is_published=False
                )
                if rank == 1:
                    res.special_award = "Winner - Certificate of Excellence"
                elif rank == 2:
                    res.special_award = "1st Runner-Up - Certificate of Excellence"
                elif rank == 3:
                    res.special_award = "2nd Runner-Up - Certificate of Excellence"
                db.session.add(res)
                rank += 1

            AuditLog.record('rankings_recalculated', 'results', actor_id=current_user.id)
            db.session.commit()
            flash('Rankings calculated from finalized evaluation scores.', 'success')

        elif action == 'toggle_publish':
            current_state = SettingsService.get_setting('results_published', 'false').lower() == 'true'
            new_state = not current_state
            SettingsService.set_setting('results_published', 'true' if new_state else 'false')

            # Mark Result records
            results_list = Result.query.all()
            for r in results_list:
                r.is_published = new_state
                r.published_at = datetime.utcnow() if new_state else None

            AuditLog.record(
                'results_publication_toggled',
                'results',
                actor_id=current_user.id,
                metadata={'published': new_state}
            )
            db.session.commit()
            flash(f"Results are now {'PUBLICLY PUBLISHED' if new_state else 'WITHHELD'}.", 'warning' if not new_state else 'success')

        return redirect(url_for('admin.results'))

    results_list = Result.query.order_by(Result.rank.asc()).all()
    results_published = SettingsService.get_setting('results_published', 'false').lower() == 'true'

    return render_template(
        'admin/results.html',
        results=results_list,
        results_published=results_published
    )


# 10. ANNOUNCEMENTS
@admin_bp.route('/announcements', methods=['GET', 'POST'])
@admin_required
def announcements():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            title = request.form.get('title', '').strip()
            message = request.form.get('message', '').strip()
            if title and message:
                ann = Announcement(
                    title=title,
                    message=message,
                    is_published=True,
                    created_by=current_user.id,
                    published_at=datetime.utcnow()
                )
                db.session.add(ann)
                AuditLog.record('announcement_created', 'announcement', title, current_user.id)
                db.session.commit()
                flash('Announcement published.', 'success')

        elif action == 'delete':
            ann_id = request.form.get('announcement_id')
            ann = Announcement.query.get_or_404(ann_id)
            db.session.delete(ann)
            AuditLog.record('announcement_deleted', 'announcement', ann_id, current_user.id)
            db.session.commit()
            flash('Announcement deleted.', 'info')

        elif action == 'toggle':
            ann_id = request.form.get('announcement_id')
            ann = Announcement.query.get_or_404(ann_id)
            ann.is_published = not ann.is_published
            db.session.commit()
            flash('Announcement status updated.', 'info')

        return redirect(url_for('admin.announcements'))

    items = Announcement.query.order_by(Announcement.published_at.desc()).all()
    return render_template('admin/announcements.html', announcements=items)


# 11. FAQS
@admin_bp.route('/faqs', methods=['GET', 'POST'])
@admin_required
def faqs():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            q = request.form.get('question', '').strip()
            a = request.form.get('answer', '').strip()
            order = int(request.form.get('display_order', 0))
            if q and a:
                faq = FAQ(question=q, answer=a, display_order=order, is_published=True)
                db.session.add(faq)
                AuditLog.record('faq_created', 'faq', actor_id=current_user.id)
                db.session.commit()
                flash('FAQ added.', 'success')

        elif action == 'delete':
            faq_id = request.form.get('faq_id')
            faq = FAQ.query.get_or_404(faq_id)
            db.session.delete(faq)
            AuditLog.record('faq_deleted', 'faq', faq_id, current_user.id)
            db.session.commit()
            flash('FAQ removed.', 'info')

        return redirect(url_for('admin.faqs'))

    items = FAQ.query.order_by(FAQ.display_order.asc(), FAQ.id.asc()).all()
    return render_template('admin/faqs.html', faqs=items)


# 12. EMAIL CONFIG & TEST
@admin_bp.route('/email', methods=['GET', 'POST'])
@admin_required
def email_notifications():
    if request.method == 'POST':
        test_recipient = request.form.get('test_recipient', '').strip()
        if test_recipient:
            success = EmailService.send_email(
                subject='Test Diagnostic Email | Prompt to Product',
                recipients=[test_recipient],
                html_body='<h3>Prompt to Product Email Service</h3><p>This is a successful test dispatch from the SSRS Group of Companies hackathon management portal.</p>'
            )
            if success:
                flash(f'Test email dispatched to {test_recipient}.', 'success')
            else:
                flash('Test email dispatch failed or SMTP is not configured in environment.', 'warning')
        return redirect(url_for('admin.email_notifications'))

    is_configured = EmailService.is_configured()
    server = current_app.config.get('MAIL_SERVER')
    port = current_app.config.get('MAIL_PORT')
    username = current_app.config.get('MAIL_USERNAME')
    tls = current_app.config.get('MAIL_USE_TLS')

    return render_template(
        'admin/email_notifications.html',
        is_configured=is_configured,
        server=server,
        port=port,
        username=username,
        tls=tls
    )


# 13. EXTERNAL LINKS (WhatsApp & Unstop)
@admin_bp.route('/links', methods=['GET', 'POST'])
@admin_required
def external_links():
    if request.method == 'POST':
        wa = request.form.get('whatsapp_group_url', '').strip()
        unstop_opp = request.form.get('unstop_opportunity_url', '').strip()
        unstop_sub = request.form.get('unstop_submission_url', '').strip()

        if wa:
            SettingsService.set_setting('whatsapp_group_url', wa)
        if unstop_opp:
            SettingsService.set_setting('unstop_opportunity_url', unstop_opp)
        if unstop_sub:
            SettingsService.set_setting('unstop_submission_url', unstop_sub)

        AuditLog.record('external_links_updated', 'settings', actor_id=current_user.id)
        flash('Official external links updated.', 'success')
        return redirect(url_for('admin.external_links'))

    settings = SettingsService.get_all_settings()
    return render_template('admin/external_links.html', settings=settings)


# 14. ADMIN USERS & PERMISSIONS
@admin_bp.route('/users', methods=['GET', 'POST'])
@super_admin_required
def admin_users():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create_admin':
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            role = request.form.get('role', 'admin')

            if not full_name or not email or not password:
                flash('All fields are required.', 'danger')
            elif User.query.filter_by(email=email).first():
                flash('User with that email already exists.', 'danger')
            else:
                user = User(
                    full_name=full_name,
                    email=email,
                    phone='0000000000',
                    college='SSRS Group of Companies Admin',
                    city='Hyderabad',
                    state='Telangana',
                    role=role if role in ['admin', 'super_admin'] else 'admin',
                    is_active=True,
                    email_verified=True
                )
                user.set_password(password)
                db.session.add(user)
                AuditLog.record('admin_user_created', 'user', email, current_user.id, {'role': user.role})
                db.session.commit()
                flash(f'New {user.role.title()} ({email}) created.', 'success')

        elif action == 'toggle_status':
            target_id = request.form.get('user_id')
            user = User.query.get_or_404(target_id)
            if user.id == current_user.id:
                flash('You cannot deactivate your own account.', 'danger')
            else:
                user.is_active = not user.is_active
                AuditLog.record('user_status_toggled', 'user', user.id, current_user.id, {'is_active': user.is_active})
                db.session.commit()
                flash(f"Account for {user.email} {'activated' if user.is_active else 'suspended'}.", 'info')

        elif action == 'change_role':
            target_id = request.form.get('user_id')
            new_role = request.form.get('new_role')
            user = User.query.get_or_404(target_id)
            if user.id == current_user.id:
                flash('You cannot change your own role.', 'danger')
            elif new_role in ['team_leader', 'admin', 'super_admin']:
                user.role = new_role
                AuditLog.record('user_role_changed', 'user', user.id, current_user.id, {'new_role': new_role})
                db.session.commit()
                flash(f'Role for {user.email} changed to {new_role}.', 'success')

        return redirect(url_for('admin.admin_users'))

    admins = User.query.filter(User.role.in_(['admin', 'super_admin'])).all()
    return render_template('admin/admin_users.html', admins=admins)


# 15. AUDIT LOGS
@admin_bp.route('/audit-logs')
@admin_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    pagination = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=25, error_out=False)
    logs = pagination.items
    return render_template('admin/audit_logs.html', logs=logs, pagination=pagination)


# 16. SYSTEM & DATABASE STATUS
@admin_bp.route('/system-status')
@admin_required
def system_status():
    db_status = 'Connected'
    mysql_version = 'Unknown'
    tables_info = []

    try:
        # Test query
        res = db.session.execute(db.text('SELECT VERSION()')).scalar()
        mysql_version = str(res)

        # Get row counts
        tables_info = [
            ('users', User.query.count()),
            ('teams', Team.query.count()),
            ('team_members', TeamMember.query.count()),
            ('submissions', Submission.query.count()),
            ('submission_history', SubmissionHistory.query.count()),
            ('problem_statements', ProblemStatement.query.count()),
            ('announcements', Announcement.query.count()),
            ('faqs', FAQ.query.count()),
            ('site_settings', SiteSetting.query.count()),
            ('audit_logs', AuditLog.query.count()),
            ('evaluations', Evaluation.query.count()),
            ('results', Result.query.count()),
        ]
    except Exception as e:
        db_status = f'Error: {str(e)}'

    return render_template(
        'admin/system_status.html',
        db_status=db_status,
        mysql_version=mysql_version,
        tables_info=tables_info
    )
